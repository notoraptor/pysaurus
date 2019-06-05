# ==============================================================================
# Copyright (C) 2019 - Philip Paquette, Steven Bocco
#
#  This program is free software: you can redistribute it and/or modify it under
#  the terms of the GNU Affero General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
#  details.
#
#  You should have received a copy of the GNU Affero General Public License along
#  with this program.  If not, see <https://www.gnu.org/licenses/>.
# ==============================================================================
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
        >>> server = Server(backup_delay_seconds=5)
        >>> server.start()

    These are public configurable server attributes. They are saved on disk at each server backup:
    - allow_user_registrations: (bool) indicate if server accepts users registrations
        (default True)
    - backup_delay_seconds: (int) number of seconds to wait between two consecutive full server backup on disk
        (default 10 minutes)
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

from pysaurus.interface.server import common, strings
from pysaurus.interface.server.connection_handler import ConnectionHandler
from pysaurus.interface.server.users import Users

LOGGER = logging.getLogger(__name__)
# Default server ping interval. # Used for sockets ping.
DEFAULT_PING_SECONDS = 30


def get_absolute_path(directory=None):
    """ Return absolute path of given directory.
        If given directory is None, return absolute path of current directory.
    """
    return os.path.abspath(directory or os.getcwd())


def get_backup_filename(filename):
    """ Return a backup filename from given filename (given filename with a special suffix). """
    return '%s.backup' % filename


def save_json_on_disk(filename, json_dict):
    """ Save given JSON dictionary into given filename and back-up previous file version if exists. """
    if os.path.exists(filename):
        os.rename(filename, get_backup_filename(filename))
    with open(filename, 'w') as file:
        json.dump(json_dict, file)


def load_json_from_disk(filename):
    """ Return a JSON dictionary loaded from given filename.
        If JSON parsing fail for given filename, try to load JSON dictionary for a backup file (if present)
        and rename backup file to given filename (backup file becomes current file versions).
        :rtype: dict
    """
    try:
        with open(filename, 'rb') as file:
            json_dict = json.load(file)
    except ValueError as exception:
        backup_filename = get_backup_filename(filename)
        if not os.path.isfile(backup_filename):
            raise exception
        with open(backup_filename, 'rb') as backup_file:
            json_dict = json.load(backup_file)
        os.rename(backup_filename, filename)
    return json_dict


def ensure_path(folder_path):
    """ Make sure given folder path exists and return given path.
        Raises an exception if path does not exists, cannot be created or is not a folder.
    """
    if not os.path.exists(folder_path):
        LOGGER.info('Creating folder %s', folder_path)
        os.makedirs(folder_path, exist_ok=True)
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        raise Exception(folder_path)
    return folder_path


class InterruptionHandler():
    """ Helper class used to save server when a system interruption signal is sent (e.g. KeyboardInterrupt). """
    __slots__ = ['server', 'previous_handler']

    def __init__(self, server):
        """ Initializer the handler.
            :param server: server to save
        """
        self.server = server  # type: Server
        self.previous_handler = signal.getsignal(signal.SIGINT)

    def handler(self, signum, frame):
        """ Handler function.
            :param signum: system signal received
            :param frame: frame received
        """
        if signum == signal.SIGINT:
            self.server.backup_now(force=True)
            if self.previous_handler:
                self.previous_handler(signum, frame)


class _ServerBackend():
    """ Class representing tornado objects used to run a server. Properties:
        - port: (integer) port where server runs.
        - application: tornado web Application object.
        - http_server: tornado HTTP server object running server code.
        - io_loop: tornado IO loop where server runs.
    """
    # pylint: disable=too-few-public-methods
    __slots__ = ['port', 'application', 'http_server', 'io_loop']

    def __init__(self):
        """ Initialize server backend. """
        self.port = None
        self.application = None
        self.http_server = None
        self.io_loop = None


class Server():
    """ Server class. """
    __slots__ = ['notifications', 'allow_registrations', 'users' 'backup_server', 'ping_seconds',
                 'users', 'backup_server', 'data_path',
                 'interruption_handler', 'backend']

    # Servers cache.
    __cache__ = {}  # {absolute path of working folder => Server}

    def __new__(cls, server_dir=None, **kwargs):
        # pylint: disable=unused-argument
        server_dir = get_absolute_path(server_dir)
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
        server_dir = get_absolute_path(server_dir)
        if server_dir in self.__class__.__cache__:
            return
        if not os.path.exists(server_dir) or not os.path.isdir(server_dir):
            raise Exception(server_dir)
        self.data_path = os.path.join(server_dir, 'data')

        # Data in memory (not stored on disk).
        self.notifications = Queue()
        self.backup_server = None
        self.interruption_handler = InterruptionHandler(self)
        # Backend objects used to run server. If None, server is not yet started.
        # Initialized when you call Server.start() (see method below).
        self.backend = None  # type: _ServerBackend

        # Database (stored on disk).
        self.allow_registrations = True
        self.ping_seconds = DEFAULT_PING_SECONDS
        self.users = None  # type: Users  # Users and administrators usernames.

        # Load data on memory.
        self._load()

        # If necessary, updated server configurable attributes from kwargs.
        self.allow_registrations = bool(kwargs.pop(strings.ALLOW_REGISTRATIONS, self.allow_registrations))
        self.ping_seconds = int(kwargs.pop(strings.PING_SECONDS, self.ping_seconds))
        assert not kwargs
        LOGGER.debug('Ping        : %s', self.ping_seconds)

        # Add server on servers cache.
        self.__class__.__cache__[server_dir] = self

    @property
    def port(self):
        """ Property: return port where this server currently runs, or None if server is not yet started. """
        return self.backend.port if self.backend else None

    def _get_server_data_filename(self):
        """ Return path to server data file name (server.json, making sure that data folder exists.
            Raises an exception if data folder does not exists and cannot be created.
        """
        return os.path.join(ensure_path(self.data_path), 'server.json')

    def _load(self):
        """ Load database from disk. """
        LOGGER.info("Loading database.")
        server_data_filename = self._get_server_data_filename()  # <server dir>/data/server.json
        if os.path.exists(server_data_filename):
            LOGGER.info("Loading server.json.")
            server_info = load_json_from_disk(server_data_filename)
            self.allow_registrations = server_info[strings.ALLOW_REGISTRATIONS]
            self.ping_seconds = server_info[strings.PING_SECONDS]
            self.users = Users.from_dict(server_info[strings.USERS])
        else:
            LOGGER.info("Creating server.json.")
            self.users = Users()
            self.backup_now(force=True)
        # Add default accounts.
        for (username, password) in (('admin', 'password'),):
            if not self.users.has_username(username):
                self.users.add_user(username, common.hash_password(password))
        # Set default admin account.
        self.users.add_admin('admin')
        LOGGER.info('Server loaded.')

    def backup_now(self, force=False):
        """ Save latest backed-up version of server data on disk.
            :param force: if True, force to save current server data even if it was not modified recently.
        """
        if force:
            self.save_data()
        if self.backup_server:
            save_json_on_disk(self._get_server_data_filename(), self.backup_server)
            self.backup_server = None
            LOGGER.info("Saved server.json.")

    @gen.coroutine
    def _task_send_notifications(self):
        """ IO loop callback: consume notifications and send it. """
        LOGGER.info('Waiting for notifications to send.')
        while True:
            connection_handler, notification = yield self.notifications.get()
            try:
                yield connection_handler.write_message(notification.json())
            except WebSocketClosedError:
                LOGGER.error('Websocket was closed while sending a notification.')
            finally:
                self.notifications.task_done()

    def set_tasks(self, io_loop: IOLoop):
        """ Set server callbacks on given IO loop. Must be called once per server before starting IO loop. """
        io_loop.add_callback(self._task_send_notifications)
        # Set callback on KeyboardInterrupt.
        signal.signal(signal.SIGINT, self.interruption_handler.handler)
        atexit.register(self.backup_now)

    def start(self, port=None, io_loop=None):
        """ Start server if not yet started. Raise an exception if server is already started.
            :param port: (optional) port where server must run. If not provided, try to start on a random
                selected port. Use property `port` to get current server port.
            :param io_loop: (optional) tornado IO lopp where server must run. If not provided, get
                default IO loop instance (tornado.ioloop.IOLoop.instance()).
        """
        if self.backend is not None:
            raise Exception('Server is already running on port %s.' % self.backend.port)
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
        self.backend = _ServerBackend()
        self.backend.application = tornado.web.Application(handlers, **settings)
        self.backend.http_server = self.backend.application.listen(port)
        self.backend.io_loop = io_loop
        self.backend.port = port
        self.set_tasks(io_loop)
        LOGGER.info('Running on port %d', self.backend.port)
        io_loop.start()

    def save_data(self):
        """ Update on-memory backup of server data. """
        self.backup_server = {
            strings.ALLOW_REGISTRATIONS: self.allow_registrations,
            strings.PING_SECONDS: self.ping_seconds,
            strings.USERS: self.users.to_dict(),
        }

    def remove_token(self, token):
        """ Disconnect given token from related user. """
        self.users.disconnect_token(token)
        self.save_data()

    def assert_token(self, token, connection_handler):
        """ Check if given token is associated to an user, check if token is still valid, and link token to given
            connection handler. If any step failed, raise an exception.
            :param token: token to check
            :param connection_handler: connection handler associated to this token
        """
        if not self.users.has_token(token):
            raise Exception()
        if self.users.token_is_alive(token):
            self.users.relaunch_token(token)
            self.save_data()
        else:
            # Logout on server side and raise exception (invalid token).
            LOGGER.error('Token too old %s', token)
            self.remove_token(token)
            raise Exception()
        self.users.attach_connection_handler(token, connection_handler)
