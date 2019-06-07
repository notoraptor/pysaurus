#!/usr/bin/env python3
""" Small module script to quickly start a server with pretty log-printing.
    You can stop the server with keyboard interruption (Ctrl+C). Usage:
    python -m diplomacy.server.run  # run on port 8432.
    python -m diplomacy.server.run --port=<given port>  # run on given port.
"""
import argparse

from tornado import gen

from pysaurus.interface.server import protocol
from pysaurus.interface.server.server import Server, DEFAULT_PORT

PARSER = argparse.ArgumentParser(description='Run server.')
PARSER.add_argument('--port', '-p', type=int, default=DEFAULT_PORT, help='server port (default: %s)' % DEFAULT_PORT)
ARGS = PARSER.parse_args()


def on_request(server, request):
    # type: (Server, protocol.Request) -> protocol.DataResponse
    print('Received', request)
    return protocol.DataResponse(
        request.request_id, 'string', 'you are %s/%s' % (request.connection_id, request.request_id))


@gen.coroutine
def on_start(server):
    # type: (Server) -> None
    print('Start')
    val = 0
    while True:
        yield gen.sleep(10)
        server.notify(protocol.Notification('a notif', val))
        val += 1


def on_exit(server):
    print('End')


def main():
    try:
        server = Server()
        server.on_request = on_request
        server.on_start = on_start
        server.on_exit = on_exit
        server.start(port=ARGS.port)
    except KeyboardInterrupt:
        print('Keyboard interruption.')


if __name__ == '__main__':
    main()
