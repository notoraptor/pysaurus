#!/usr/bin/env python3
""" Small module script to quickly start a server with pretty log-printing.
    You can stop the server with keyboard interruption (Ctrl+C). Usage:
    python -m diplomacy.server.run  # run on port 8432.
    python -m diplomacy.server.run --port=<given port>  # run on given port.
"""
import argparse

from pysaurus.interface.server.server import Server

DEFAULT_PORT = 8432
PARSER = argparse.ArgumentParser(description='Run server.')
PARSER.add_argument('--port', '-p', type=int, default=DEFAULT_PORT,
                    help='run on the given port (default: %s)' % DEFAULT_PORT)
ARGS = PARSER.parse_args()

try:
    Server().start(port=ARGS.port)
except KeyboardInterrupt:
    print('Keyboard interruption.')
