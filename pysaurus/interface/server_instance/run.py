#!/usr/bin/env python3
import argparse
import asyncio
import queue
import traceback

from pysaurus.interface.server import protocol
from pysaurus.interface.server.server import Server, DEFAULT_PORT
from pysaurus.interface.server_instance.request_manager import REQUEST_MANAGER
from pysaurus.interface.server_instance.server_context import ServerContext


async def monitor_context_collector(server):
    # type: (Server) -> None
    print('Monitoring notifications collector.')
    context = server.context  # type: ServerContext
    while True:
        try:
            notification = context.collector.queue.get_nowait()
            await server.notify(protocol.Notification(name=type(notification).__name__,
                                                      parameters=notification.to_dict()))
        except queue.Empty:
            await asyncio.sleep(1)
        except Exception as exc:
            print('Exception while sending notification:')
            traceback.print_tb(exc.__traceback__)
            print(type(exc).__name__)
            print(exc)
            print()


def on_start(server):
    # type: (Server) -> None
    server.launch(monitor_context_collector)


def on_exit(server):
    print('Server closed.')


async def on_request(server, request):
    # type: (Server, protocol.Request) -> protocol.DataResponse
    return await REQUEST_MANAGER.manage_request(server, request)


def main():
    parser = argparse.ArgumentParser(description='Run server.')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT, help='server port (default %s)' % DEFAULT_PORT)
    args = parser.parse_args()
    try:
        server = Server(context=ServerContext())
        server.on_request = on_request
        server.on_start = on_start
        server.on_exit = on_exit
        server.start(port=args.port)
    except KeyboardInterrupt:
        print('Keyboard interruption.')


if __name__ == '__main__':
    main()
