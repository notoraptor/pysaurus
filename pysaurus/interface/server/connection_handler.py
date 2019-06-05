""" Tornado connection handler class, used internally to manage data received by server application. """
import logging
from urllib.parse import urlparse

import ujson as json
from tornado import gen
from tornado.websocket import WebSocketHandler, WebSocketClosedError

REQUEST_ID = 'request_id'

LOGGER = logging.getLogger(__name__)


def response_error(exc, request_id):
    pass


def request_parse(json_request):
    pass


def request_handle(server, request, self):
    pass


def response_ok(request_id):
    pass


class ConnectionHandler(WebSocketHandler):
    """ ConnectionHandler class. Properties:
        - server: server object representing running server.
    """

    # pylint: disable=abstract-method

    def __init__(self, *args, **kwargs):
        self.server = None
        super(ConnectionHandler, self).__init__(*args, **kwargs)

    def initialize(self, server=None):
        """ Initialize the connection handler.
            :param server: a Server object.
            :type server: diplomacy.Server
        """
        # pylint: disable=arguments-differ
        if self.server is None:
            self.server = server

    def get_compression_options(self):
        """ Return compression options for the connection (see parent method).
            Non-None enables compression with default options.
        """
        return {}

    def check_origin(self, origin):
        """ Return True if we should accept connexion from given origin (str). """

        # It seems origin may be 'null', e.g. if client is a web page loaded from disk (`file:///my_test_file.html`).
        # Accept it.
        if origin == 'null':
            return True

        # Try to check if origin matches host (without regarding port).
        # Adapted from parent method code (tornado 4.5.3).
        parsed_origin = urlparse(origin)
        origin = parsed_origin.netloc.split(':')[0]
        origin = origin.lower()
        # Split host with ':' and keep only first piece to ignore eventual port.
        host = self.request.headers.get("Host").split(':')[0]
        return origin == host

    def on_close(self):
        """ Invoked when the socket is closed (see parent method).
            Detach this connection handler from server users.
        """
        self.server.users.remove_connection(self, remove_tokens=False)
        LOGGER.info("Removed connection. Remaining %d connection(s).", self.server.users.count_connections())

    @gen.coroutine
    def on_message(self, message):
        """ Parse given message and manage parsed data (expected a string representation of a request). """
        try:
            json_request = json.loads(message)
            if not isinstance(json_request, dict):
                raise ValueError("Unable to convert a JSON string to a dictionary.")
        except ValueError as exc:
            # Error occurred because either message is not a JSON string or parsed JSON object is not a dict.
            response = response_error(exc, request_id=None)
            pass
        else:
            try:
                request = request_parse(json_request)
                # Link request token to this connection handler.
                self.server.users.attach_connection_handler(request.token, self)
                response = request_handle(self.server, request, self)
                if response is None:
                    response = response_ok(request_id=request.request_id)
            except Exception as exc:
                response = response_error(exc, request_id=json_request.get(REQUEST_ID, None))
        try:
            yield self.write_message(response.json())
        except WebSocketClosedError:
            LOGGER.error('Websocket is closed.')
