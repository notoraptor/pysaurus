#!/usr/bin/env python3
import argparse
import asyncio
import queue
import traceback

from pysaurus.interface.cefgui.gui_api import GuiAPI
from pysaurus.interface.server import protocol
from pysaurus.interface.server.protocol import AutoErrorResponse
from pysaurus.interface.server.server import DEFAULT_PORT, Server


class ErrroUnknownRequest(AutoErrorResponse):
    def __init__(self, request: protocol.Request):
        super(ErrroUnknownRequest, self).__init__(request.request_id, request.name)


class Interface(GuiAPI):
    def __init__(self, server):
        super().__init__()
        self.server = server

    def _notify(self, notification):
        # self.server.notify(
        #     protocol.Notification(
        #         name=type(notification).__name__, parameters=notification.to_dict()
        #     )
        # )
        pass


async def monitor_context_collector(server):
    # type: (Server) -> None
    print("Monitoring notifications collector.")
    context = server.context  # type: Interface
    while True:
        try:
            notification = context.notifier.queue.get_nowait()
            await server.notify(
                protocol.Notification(
                    name=type(notification).__name__,
                    parameters={
                        "name": type(notification).__name__,
                        "notification": notification.to_dict(),
                        "message": str(notification),
                    },
                )
            )
        except queue.Empty:
            await asyncio.sleep(0.01)
        except Exception as exc:
            print("Exception while sending notification:")
            traceback.print_tb(exc.__traceback__)
            print(type(exc).__name__)
            print(exc)
            print()


def on_start(server):
    # type: (Server) -> None
    server.launch(monitor_context_collector)


def on_exit(server):
    print("Server closed.")


def on_request(server: Server, request: protocol.Request) -> protocol.Response:
    print("Received", request)
    func = getattr(server.context, request.name, None)
    if callable(func) and not request.name.startswith("_"):
        return protocol.DataResponse.from_request(request, func(*request.parameters))
    return ErrroUnknownRequest(request)


def main():
    parser = argparse.ArgumentParser(description="Run server.")
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=DEFAULT_PORT,
        help=f"server port (default {DEFAULT_PORT})",
    )
    args = parser.parse_args()
    try:
        server = Server()
        server.context = Interface(server)
        server.on_request = on_request
        server.on_start = on_start
        server.on_exit = on_exit
        server.start(port=args.port)
    except KeyboardInterrupt:
        print("Keyboard interruption.")


if __name__ == "__main__":
    main()
