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

    You can also configure some server attributes when instantiating it:
        >>> from pysaurus.interface.server.server import Server
        >>> server = Server(ping_seconds=10)
        >>> server.start()

    These are public configurable server attributes. They are saved on disk at each server backup:
        (default True)
    - ping_seconds: (int) ping period used by server to check is connected sockets are alive.
"""
import atexit
import logging
import os
import signal

import tornado
import tornado.web
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.queues import Queue
from tornado.websocket import WebSocketClosedError

from pysaurus.interface.server import common
from pysaurus.interface.server.connection_handler import ConnectionHandler

DEFAULT_PING_SECONDS = 30
LOGGER = logging.getLogger(__name__)


class Notification:
    def __init__(self, connection_handler, notification):
        self.connection_handler = connection_handler
        self.notification = notification


class Server():
    """ Server class. """
    __slots__ = ['notifications', 'data_path', 'previous_signal_handler', 'ping_seconds', 'on_exit',
                 'port', 'application', 'http_server', 'io_loop']

    # Servers cache.
    __cache__ = {}  # {absolute path of working folder => Server}

    def __new__(cls, server_dir=None, **kwargs):
        # pylint: disable=unused-argument
        server_dir = Server._get_absolute_path(server_dir)
        if server_dir in cls.__cache__:
            server = cls.__cache__[server_dir]
        else:
            server = object.__new__(cls)
            cls.__cache__[server_dir] = server
        return server

    def __init__(self, server_dir=None, ping_seconds=None, on_exit=None):
        """ Initialize the server.
            :param server_dir: path of folder in (from) which server data will be saved (loaded).
                If None, working directory (where script is executed) will be used.
        """

        # File paths and attributes related to database.
        server_dir = Server._get_absolute_path(server_dir)
        if server_dir in self.__class__.__cache__:
            return
        if not os.path.isdir(server_dir):
            raise Exception('Server path is not a directory: %s' % server_dir)
        self.data_path = os.path.join(server_dir, 'data')
        self.notifications = Queue()
        self.previous_signal_handler = signal.getsignal(signal.SIGINT)
        self.port = None
        self.application = None
        self.http_server = None
        self.io_loop = None
        self.ping_seconds = ping_seconds or DEFAULT_PING_SECONDS
        self.on_exit = on_exit if callable(on_exit) else None
        LOGGER.debug('Ping        : %s', self.ping_seconds)

    @staticmethod
    def _get_absolute_path(directory=None):
        """ Return absolute path of given directory.
            If given directory is None, return absolute path of current directory.
        """
        return os.path.abspath(directory or os.getcwd())

    @gen.coroutine
    def _task_send_notifications(self):
        """ IO loop callback: consume notifications and send it. """
        LOGGER.info('Waiting for notifications to send.')
        while True:
            message = yield self.notifications.get()  # type: Notification
            try:
                yield message.connection_handler.write_message(message.notification.json())
            except WebSocketClosedError:
                LOGGER.error('Websocket was closed while sending a notification.')
            finally:
                self.notifications.task_done()

    def _handle_interruption(self, signum, frame):
        """ Handler function.
            :param signum: system signal received
            :param frame: frame received
        """
        if signum == signal.SIGINT:
            if self.on_exit:
                self.on_exit()
            if self.previous_signal_handler:
                self.previous_signal_handler(signum, frame)

    def _set_tasks(self, io_loop: IOLoop):
        """ Set server callbacks on given IO loop. Must be called once per server before starting IO loop. """
        io_loop.add_callback(self._task_send_notifications)
        # Set callback on KeyboardInterrupt.
        signal.signal(signal.SIGINT, self._handle_interruption)
        if self.on_exit:
            atexit.register(self.on_exit)

    def start(self, port=None, io_loop=None):
        """ Start server if not yet started. Raise an exception if server is already started.
            :param port: (optional) port where server must run. If not provided, try to start on a random
                selected port. Use property `port` to get current server port.
            :param io_loop: (optional) tornado IO lopp where server must run. If not provided, get
                default IO loop instance (tornado.ioloop.IOLoop.instance()).
        """
        if self.port is not None:
            raise Exception('Server is already running on port %s.' % self.port)
        if port is None:
            port = 8432
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
        self.application = tornado.web.Application(handlers, **settings)
        self.http_server = self.application.listen(port)
        self.io_loop = io_loop
        self.port = port
        self._set_tasks(io_loop)
        LOGGER.info('Running on port %d', self.port)
        io_loop.start()

    def notify(self, connection_handler, notification):
        # todo
        self.notifications.put(Notification(connection_handler, notification))
