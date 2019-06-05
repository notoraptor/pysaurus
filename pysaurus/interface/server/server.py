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
        >>> server = Server(allow_user_registrations=False)
        >>> server.start()

    These are public configurable server attributes. They are saved on disk at each server backup:
    - allow_user_registrations: (bool) indicate if server accepts users registrations
        (default True)
    - ping_seconds: (int) ping period used by server to check is connected sockets are alive.
"""
import atexit
import logging
import os
import signal

import tornado
import tornado.web
import ujson as json
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.queues import Queue
from tornado.websocket import WebSocketClosedError

from pysaurus.interface.server import common
from pysaurus.interface.server.connection_handler import ConnectionHandler
from pysaurus.interface.server.users import Users

DEFAULT_PING_SECONDS = 30
ALLOW_REGISTRATIONS = 'allow_registrations'
PING_SECONDS = 'ping_seconds'
USERS = 'users'
LOGGER = logging.getLogger(__name__)


class Notification:
    def __init__(self, connection_handler, notification):
        self.connection_handler = connection_handler
        self.notification = notification


class Server():
    """ Server class. """
    __slots__ = ['notifications', 'users', 'data_path', 'previous_signal_handler',
                 'allow_registrations', 'ping_seconds', 'port', 'application', 'http_server', 'io_loop']

    users: Users

    # Servers cache.
    __cache__ = {}  # {absolute path of working folder => Server}

    def __new__(cls, server_dir=None, **kwargs):
        # pylint: disable=unused-argument
        server_dir = Server._get_absolute_path(server_dir)
        if server_dir in cls.__cache__:
            server = cls.__cache__[server_dir]
        else:
            server = object.__new__(cls)
        return server

    def __init__(self, server_dir=None, **kwargs):
        """ Initialize the server.
            :param server_dir: path of folder in (from) which server data will be saved (loaded).
                If None, working directory (where script is executed) will be used.
            :param kwargs: (optional) values for some public configurable server attributes.
                Given values will overwrite values saved on disk.
            Server data is stored in folder `<working directory>/data`.
        """

        # File paths and attributes related to database.
        server_dir = Server._get_absolute_path(server_dir)
        if server_dir in self.__class__.__cache__:
            return
        if not os.path.isdir(server_dir):
            raise Exception('Server path is not a directory: %s' % server_dir)
        self.data_path = os.path.join(server_dir, 'data')

        # Data in memory (not stored on disk).
        self.notifications = Queue()
        self.previous_signal_handler = signal.getsignal(signal.SIGINT)
        self.port = None
        self.application = None
        self.http_server = None
        self.io_loop = None

        # Database (stored on disk).
        self.allow_registrations = True
        self.ping_seconds = DEFAULT_PING_SECONDS
        self.users = None

        # Load data on memory.
        self._load()

        # If necessary, updated server configurable attributes from kwargs.
        self.allow_registrations = bool(kwargs.pop(ALLOW_REGISTRATIONS, self.allow_registrations))
        self.ping_seconds = int(kwargs.pop(PING_SECONDS, self.ping_seconds))
        assert not kwargs
        LOGGER.debug('Ping        : %s', self.ping_seconds)

        # Add server on servers cache.
        self.__class__.__cache__[server_dir] = self

    @staticmethod
    def _get_absolute_path(directory=None):
        """ Return absolute path of given directory.
            If given directory is None, return absolute path of current directory.
        """
        return os.path.abspath(directory or os.getcwd())

    def _load(self):
        """ Load database from disk. """
        to_be_saved = False
        LOGGER.info("Loading database.")
        server_data_filename = self._get_server_data_filename()  # <server dir>/data/server.json
        if os.path.exists(server_data_filename):
            LOGGER.info("Loading server.json.")
            with open(server_data_filename, 'rb') as file:
                server_info = json.load(file)
            self.allow_registrations = server_info[ALLOW_REGISTRATIONS]
            self.ping_seconds = server_info[PING_SECONDS]
            self.users = Users.from_dict(server_info[USERS])
        else:
            LOGGER.info("Creating server.json.")
            self.users = Users()
            to_be_saved = True
        # Add default accounts.
        if not self.users.has_admins():
            self.users.add_user('admin', common.hash_password('password'))
            # Set default admin account.
            self.users.add_admin('admin')
            to_be_saved = True
        if to_be_saved:
            self.backup_now()
        LOGGER.info('Server loaded.')

    def _get_server_data_filename(self):
        """ Return path to server data file name (server.json, making sure that data folder exists.
            Raises an exception if data folder does not exists and cannot be created.
        """
        return os.path.join(common.ensure_path(self.data_path), 'server.json')

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
            self.backup_now()
            if self.previous_signal_handler:
                self.previous_signal_handler(signum, frame)

    def _set_tasks(self, io_loop: IOLoop):
        """ Set server callbacks on given IO loop. Must be called once per server before starting IO loop. """
        io_loop.add_callback(self._task_send_notifications)
        # Set callback on KeyboardInterrupt.
        signal.signal(signal.SIGINT, self._handle_interruption)
        atexit.register(self.backup_now)

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

    def assert_token(self, token, connection_handler):
        """ Check if given token is associated to an user, check if token is still valid, and link token to given
            connection handler. If any step failed, raise an exception.
            :param token: token to check
            :param connection_handler: connection handler associated to this token
        """
        if not self.users.has_token(token):
            raise Exception('Unknown token %s' % token)
        if self.users.token_is_alive(token):
            self.users.relaunch_token(token)
            self.backup_now()
        else:
            # Logout on server side and raise exception (invalid token).
            LOGGER.error('Token too old %s', token)
            self.remove_token(token)
            self.backup_now()
            raise Exception('Token too old %s' % token)
        self.users.attach_connection_handler(token, connection_handler)

    def remove_token(self, token):
        """ Disconnect given token from related user. """
        self.users.disconnect_token(token)
        self.backup_now()

    def backup_now(self):
        """ Save latest backed-up version of server data on disk. """
        data_to_save = {
            ALLOW_REGISTRATIONS: self.allow_registrations,
            PING_SECONDS: self.ping_seconds,
            USERS: self.users.to_dict(),
        }
        with open(self._get_server_data_filename(), 'w') as file:
            json.dump(data_to_save, file)
        LOGGER.info("Saved server.json.")

    def notify(self, connection_handler, notification):
        # todo
        self.notifications.put(Notification(connection_handler, notification))
