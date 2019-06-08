#!/usr/bin/env python3
""" Small module script to quickly start a server with pretty log-printing.
    You can stop the server with keyboard interruption (Ctrl+C). Usage:
    python -m diplomacy.server.run  # run on port 8432.
    python -m diplomacy.server.run --port=<given port>  # run on given port.
"""
import argparse

from tornado.queues import Queue

from pysaurus.core import notifications
from pysaurus.core.notifier import Notifier
from pysaurus.interface.common.interface import Interface
from pysaurus.interface.server import protocol
from pysaurus.interface.server.server import Server, DEFAULT_PORT


class NotificationCollector:
    def __init__(self, notifier):
        # type: (Notifier) -> None
        self.queue = Queue()
        notifier.set_default_manager(self.collect)

    def collect(self, notification):
        # type: (notifications.Notification) -> None
        print('Notified', type(notification).__name__)
        name = type(notification).__name__
        parameters = notification.to_dict()
        self.queue.put_nowait(protocol.Notification(name=name, parameters=parameters))
        print('Notification registered into queue, now', self.queue.qsize(), 'element(s).')


class ServerInterface:
    def __init__(self):
        self.interface = None
        self.notifier = Notifier()
        self.notification_collector = NotificationCollector(self.notifier)

    def load_database(self, server):
        self.interface = Interface(self.notifier)

    async def consume_queue(self, server):
        print('Consuming queue.')
        while True:
            try:
                element = await self.notification_collector.queue.get()
                await server.notify(element)
            except Exception as exc:
                print('Exception while sending notifications', exc)
            finally:
                self.notification_collector.queue.task_done()

    def on_request(self, server, request):
        # type: (Server, protocol.Request) -> protocol.DataResponse
        print('Received', request)
        if self.interface:
            return protocol.DataResponse(request.request_id, 'string', 'Database already loaded')
        server.launch(self.load_database)
        return protocol.DataResponse(request.request_id, 'string', 'Loading database')

    def on_start(self, server):
        # type: (Server) -> None
        print('Starting server.')
        server.launch(self.consume_queue)

    def on_exit(self, server):
        print('Server closed.')


def main():
    parser = argparse.ArgumentParser(description='Run server.')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT,
                        help='server port (default: %s)' % DEFAULT_PORT)
    args = parser.parse_args()
    try:
        server = Server()
        server_interface = ServerInterface()
        server.on_request = server_interface.on_request
        server.on_start = server_interface.on_start
        server.on_exit = server_interface.on_exit
        server.start(port=args.port)
    except KeyboardInterrupt:
        print('Keyboard interruption.')


if __name__ == '__main__':
    main()
