#!/usr/bin/env python3
""" Small module script to quickly start a server with pretty log-printing.
    You can stop the server with keyboard interruption (Ctrl+C). Usage:
    python -m diplomacy.server.run  # run on port 8432.
    python -m diplomacy.server.run --port=<given port>  # run on given port.
"""
import argparse

from tornado import gen

from pysaurus.core import notifications
from pysaurus.core.notifier import Notifier
from pysaurus.interface.common.interface import Interface
from pysaurus.interface.server import protocol
from pysaurus.interface.server.server import Server, DEFAULT_PORT

PARSER = argparse.ArgumentParser(description='Run server.')
PARSER.add_argument('--port', '-p', type=int, default=DEFAULT_PORT, help='server port (default: %s)' % DEFAULT_PORT)
ARGS = PARSER.parse_args()

_server = None
_interface = None


class ServerInterface:
    __slots__ = ('notifier',)

    def __init__(self):
        self.notifier = None
        self.notifier = Notifier()
        self.notifier.set_default_manager(self.handle_core_notification)

    def load_database(self):
        global _interface
        _interface = Interface.load_database(self.notifier)

    def handle_core_notification(self, notification):
        # type: (notifications.Notification) -> None
        global _server
        print('Got', type(notification).__name__)
        if _server:
            name = type(notification).__name__
            parameters = notification.to_dict()
            _server.notify(protocol.Notification(name=name, parameters=parameters))

    def on_request(self, server, request):
        # type: (Server, protocol.Request) -> protocol.DataResponse
        global _interface
        print('Received', request)
        if _interface:
            return protocol.DataResponse(
                request.request_id, 'string', 'Database already loaded')
        else:
            server.launch(self.load_database)
            return protocol.DataResponse(
                request.request_id, 'string', 'Loading database')

    @gen.coroutine
    def on_start(self, server):
        # type: (Server) -> None
        global _server
        print('Start')
        _server = server

    def on_exit(self, server):
        print('End')


def main():
    try:
        server = Server()
        server_interface = ServerInterface()
        server.on_request = server_interface.on_request
        server.on_start = server_interface.on_start
        server.on_exit = server_interface.on_exit
        server.start(port=ARGS.port)
    except KeyboardInterrupt:
        print('Keyboard interruption.')


if __name__ == '__main__':
    main()
