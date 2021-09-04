""" Concret standalone server object. Manages and save server data, send notifications,
    receives requests and send responses.

    Example:
        >>> from pysaurus.interface.server.server import Server
        >>> Server().start(port=1234)  # If port is not given, a random port will be selected.

    You can interrupt server by sending a keyboard interrupt signal (Ctrl+C).
        >>> from pysaurus.interface.server.server import Server
        >>> try:
        >>>     Server().start()
        >>> except KeyboardInterrupt:
        >>>     print('Server interrupted.')
"""
import asyncio
import atexit
import os
import signal
from typing import Union

import tornado
import tornado.web
import ujson as json
from tornado.gen import multi
from tornado.ioloop import IOLoop
from tornado.queues import Future, Queue
from tornado.websocket import WebSocketClosedError

from pysaurus.interface.server import common, protocol
from pysaurus.interface.server.connection_handler import ConnectionHandler
from pysaurus.interface.server.connection_manager import ConnectionManager

DEFAULT_PORT = 8432
DEFAULT_PING_SECONDS = 60


class Server(ConnectionManager):
    """ Server class. """
    __slots__ = [
        # private fields
        '__notifications', '__path', '__previous_signal_handler',
        '__port', '__application', '__http_server', '__io_loop',
        # public fields, to be directly set after creating server object, before calling start().
        # callbacks.
        'on_start', 'on_exit', 'on_connection_open', 'on_connection_close', 'on_request',
        # options.
        'ping_seconds', 'context'
    ]

    # Servers cache.
    __cache__ = {}  # {absolute path of working folder => Server}

    def __new__(cls, server_dir=None, **kwargs):
        server_dir = Server._get_absolute_path(server_dir)
        if server_dir not in cls.__cache__:
            Server.log('Creating new server.')
            cls.__cache__[server_dir] = object.__new__(cls)
        else:
            Server.log('Using existing server.')
        return cls.__cache__[server_dir]

    def __init__(self, server_dir=None, context=None):
        """ Initialize the server.
            :param server_dir: path of folder in (from) which server data will be saved (loaded).
                If None, working directory (where script is executed) will be used.
        """
        # File paths and attributes related to database.
        server_dir = Server._get_absolute_path(server_dir)
        if not os.path.isdir(server_dir):
            raise Exception('Server path is not a directory: %s' % server_dir)
        super(Server, self).__init__()
        self.__path = os.path.join(server_dir, 'data')
        self.__notifications = Queue()
        self.__previous_signal_handler = signal.getsignal(signal.SIGINT)
        self.__port = None
        self.__application = None
        self.__http_server = None
        self.__io_loop = None

        self.ping_seconds = DEFAULT_PING_SECONDS
        self.context = context

        # (server) -> None
        self.on_start = None
        # (server) -> None
        self.on_exit = None
        # (server, connection_id) -> None
        self.on_connection_open = None
        # (server, connection_id) -> None
        self.on_connection_close = None
        # (server, request) -> response | None
        self.on_request = None

        signal.signal(signal.SIGINT, signal.SIG_DFL)

    @property
    def io_loop(self):
        return self.__io_loop

    @staticmethod
    def log(*args, **kwargs):
        print('[server]', *args, **kwargs)

    @staticmethod
    def _get_absolute_path(directory=None):
        """ Return absolute path of given directory.
            If given directory is None, return absolute path of current directory.
        """
        return os.path.abspath(directory or os.getcwd())

    async def _send_notification(self, notification):
        # type: (protocol.Notification) -> None
        if notification.connection_id is not None:
            connection_handler = self._get_connection_handler(notification.connection_id)
            if not connection_handler:
                Server.log('Notification: unknown connection ID %d' % notification.connection_id)
            else:
                await connection_handler.write_message(json.dumps(notification.to_dict()))
                Server.log('To %d: %s' % (notification.connection_id, notification))
        else:
            sending = []
            for connection_id, connection_handler in self._connections():
                notification_dict = notification.to_dict(connection_id=connection_id)
                future_sending = connection_handler.write_message(json.dumps(notification_dict))
                sending.append(future_sending)
            await multi(sending)
            Server.log('To everyone: %s' % notification.name)

    async def _producer(self):
        """ IO loop callback: consume notifications and send it. """
        Server.log('Waiting notifications.')
        while True:
            # todo
            notification = await self.__notifications.get()
            try:
                await self._send_notification(notification)
            except WebSocketClosedError:
                Server.log('Websocket was closed while sending a notification.')
            finally:
                self.__notifications.task_done()

    async def _call_on_start(self):
        if self.on_start:
            await asyncio.coroutine(self.on_start)(self)

    def _call_on_exit(self):
        if self.on_exit:
            self.on_exit(self)

    def _call_on_connection_open(self, connection_id):
        if self.on_connection_open:
            self.on_connection_open(self, connection_id)

    def _call_on_connection_close(self, connection_id):
        if self.on_connection_close:
            self.on_connection_close(self, connection_id)

    def _set_tasks(self, io_loop: IOLoop):
        """ Set server callbacks on given IO loop. Must be called once per server before starting IO loop. """
        io_loop.add_callback(self._producer)
        io_loop.add_callback(self._call_on_start)
        # Set callback on KeyboardInterrupt.
        # signal.signal(signal.SIGINT, self._handle_interruption)
        atexit.register(self._call_on_exit)

    def launch(self, function):
        if self.__io_loop:
            self.__io_loop.add_callback(function, self)

    def start(self, port=None, io_loop=None):
        """ Start server if not yet started. Raise an exception if server is already started.
            :param port: (optional) port where server must run. If not provided, try to start on a random
                selected port. Use property `port` to get current server port.
            :param io_loop: (optional) tornado IO lopp where server must run. If not provided, get
                default IO loop instance (tornado.ioloop.IOLoop.instance()).
        """
        if self.__port is not None:
            raise Exception('Server is already running on port %s.' % self.__port)
        if port is None:
            port = DEFAULT_PORT
        if io_loop is None:
            io_loop = tornado.ioloop.IOLoop.instance()
        handlers = [
            tornado.web.url(r"/", ConnectionHandler, {'server': self}),
        ]
        settings = {
            'cookie_secret': common.generate_token(),
            'xsrf_cookies': True,
            'websocket_ping_interval': self.ping_seconds,
            'websocket_ping_timeout': 2 * self.ping_seconds,
            'websocket_max_message_size': 64 * 1024 * 1024
        }
        self.__application = tornado.web.Application(handlers, **settings)
        self.__http_server = self.__application.listen(port)
        self.__io_loop = io_loop
        self.__port = port
        self._set_tasks(io_loop)
        Server.log('Ping: %d' % self.ping_seconds)
        Server.log('Port: %d' % self.__port)
        io_loop.start()

    def notify(self, notification):
        # type: (protocol.Notification) -> Future[None]
        return self.__notifications.put(notification)

    def open_connection(self, connection_handler):
        self._add_connection(connection_handler)
        connection_id = self.get_connection_id(connection_handler)
        self._call_on_connection_open(connection_id)

    def close_connection(self, connection_handler):
        connection_id = self.get_connection_id(connection_handler)
        self._remove_connection(connection_handler)
        self._call_on_connection_close(connection_id)

    async def manage_request(self, request):
        # type: (protocol.Request) -> Union[protocol.OkResponse, protocol.ErrorResponse, protocol.DataResponse, None]
        if self.on_request:
            return await asyncio.coroutine(self.on_request)(self, request)
