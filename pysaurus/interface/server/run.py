#!/usr/bin/env python3
""" Small module script to quickly start a server with pretty log-printing.
    You can stop the server with keyboard interruption (Ctrl+C). Usage:
    python -m diplomacy.server.run  # run on port 8432.
    python -m diplomacy.server.run --port=<given port>  # run on given port.
"""
import argparse

from pysaurus.core import notifications
from pysaurus.core.notifier import Notifier
from pysaurus.interface.common.interface import Interface
from pysaurus.interface.server import protocol
from pysaurus.interface.server.server import Server, DEFAULT_PORT

PARSER = argparse.ArgumentParser(description='Run server.')
PARSER.add_argument('--port', '-p', type=int, default=DEFAULT_PORT, help='server port (default: %s)' % DEFAULT_PORT)
ARGS = PARSER.parse_args()


class ServerData:
    server = None
    interface = None
    notifier = None
    @staticmethod
    def init(server):
        ServerData.server = server
        ServerData.notifier = Notifier()


class ServerInterface:
    __slots__ = ('notifier',)

    def __init__(self):
        ServerData.notifier.set_default_manager(self.handle_core_notification)

    def load_database(self):
        ServerData.interface = Interface(ServerData.notifier)

    def handle_core_notification(self, notification):
        # type: (notifications.Notification) -> None
        print('Notified', type(notification).__name__)
        name = type(notification).__name__
        parameters = notification.to_dict()
        ServerData.server.notify(protocol.Notification(name=name, parameters=parameters))

    def on_request(self, server, request):
        # type: (Server, protocol.Request) -> protocol.DataResponse
        print('Received', request)
        if ServerData.interface:
            return protocol.DataResponse(request.request_id, 'string', 'Database already loaded')
        server.launch(self.load_database)
        return protocol.DataResponse(request.request_id, 'string', 'Loading database')

    def on_start(self, server):
        # type: (Server) -> None
        print('Starting server.')

    def on_exit(self, server):
        print('Server closed.')


def main():
    try:
        server = Server()
        ServerData.init(server)
        server_interface = ServerInterface()
        server.on_request = server_interface.on_request
        server.on_start = server_interface.on_start
        server.on_exit = server_interface.on_exit
        server.start(port=ARGS.port)
    except KeyboardInterrupt:
        print('Keyboard interruption.')


if __name__ == '__main__':
    main()
