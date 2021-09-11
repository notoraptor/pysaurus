"""
Tornado connection handler class,
used internally to manage data received by server application.
"""
import traceback
from urllib.parse import urlparse

import ujson as json
from tornado.websocket import WebSocketClosedError, WebSocketHandler

from pysaurus.application.exceptions import PysaurusError
from pysaurus.interface.websockets.server import protocol

REQUEST_ID = "request_id"


EQUIV = {
    "127.0.0.1": "localhost"
}


class ConnectionHandler(WebSocketHandler):
    """
    ConnectionHandler class. Properties:
    - server: server object representing running server.
    """

    def __init__(self, *args, **kwargs):
        from pysaurus.interface.websockets.server.server import Server

        self.server = None  # type: Server
        super(ConnectionHandler, self).__init__(*args, **kwargs)

    def initialize(self, server=None):
        """Initialize the connection handler.
        :param server: a Server object.
        :type server: diplomacy.Server
        """
        self.server = server

    def get_compression_options(self):
        """Return compression options for the connection (see parent method).
        Non-None enables compression with default options.
        """
        return {}

    def check_origin(self, origin):
        """Return True if we should accept connexion from given origin (str)."""

        # It seems origin may be 'null', e.g. if client is a web page loaded from disk
        # (`file:///my_test_file.html`).
        # Accept it.
        if origin == "null":
            return True

        # Try to check if origin matches host (without regarding port).
        # Adapted from parent method code (tornado 4.5.3).
        parsed_origin = urlparse(origin)
        origin = parsed_origin.netloc.split(":")[0]
        origin = origin.lower()
        # Split host with ':' and keep only first piece to ignore eventual port.
        host = self.request.headers.get("Host").split(":")[0]
        return EQUIV.get(origin, origin) == EQUIV.get(host, host)

    def open(self):
        self.server.open_connection(self)
        print(
            "New web socket, now %d connection(s)." % (self.server.count_connections())
        )

    def on_close(self):
        """Invoked when the socket is closed (see parent method).
        Detach this connection handler from server users.
        """
        self.server.close_connection(self)
        print(
            "Web socket closed, now %d connection(s)." % self.server.count_connections()
        )

    async def on_message(self, message):
        """
        Parse given message and manage parsed data
        (expected a string representation of a request).
        """
        try:
            json_request = json.loads(message)
            if not isinstance(json_request, dict):
                raise ValueError("Unable to convert a JSON string to a dictionary.")
        except ValueError as exc:
            # Error occurred because either message is not a JSON string
            # or parsed JSON object is not a dict.
            response = protocol.ErrorResponse.from_exception("", exc)
        else:
            try:
                json_request["connection_id"] = self.server.get_connection_id(self)
                request = protocol.Request.from_dict(json_request)
                response = self.server.manage_request(
                    request
                ) or protocol.OkResponse(request.request_id)
            except PysaurusError as exc:
                response = protocol.ErrorResponse.from_exception(
                    json_request.get(REQUEST_ID, ""), exc
                )
            except Exception as exc:
                print("<INTERNAL_ERROR>")
                response = protocol.ErrorResponse(
                    json_request.get(REQUEST_ID, ""), "Exception", "Internal error."
                )
                traceback.print_tb(exc.__traceback__)
                print(type(exc).__name__)
                print(exc)
                print("</INTERNAL_ERROR>")
        try:
            await self.write_message(json.dumps(response.to_dict()))
        except WebSocketClosedError:
            print("Web socket is closed.")
