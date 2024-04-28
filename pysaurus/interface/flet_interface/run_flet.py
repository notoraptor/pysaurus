import asyncio
import sys
import traceback
from typing import Optional

import flet as ft

from pysaurus.application import exceptions
from pysaurus.core.enumeration import EnumerationError
from pysaurus.core.functions import string_to_pieces
from pysaurus.interface.flet_interface.api_for_flet import ApiForFlet
from pysaurus.interface.flet_interface.flet_api_interface import FletApiInterface
from pysaurus.interface.flet_interface.page.homepage import Homepage


class App:
    __slots__ = ("interface", "page", "exit_code")

    def __init__(self):
        self.interface: Optional[FletApiInterface] = None
        self.page: Optional[ft.Page] = None
        self.exit_code = 0

    def run(self, page: ft.Page):
        self.page = page
        self.interface = FletApiInterface(ApiForFlet(page))
        db_names = self.interface.get_database_names()

        page.data = self.interface
        page.title = "Pysaurus"
        page.add(ft.Container(Homepage(page, db_names), expand=True))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.interface
        self.interface.close_app()

    def exception_handler(self, loop, ctx):
        exception = ctx["exception"]
        if isinstance(exception, (OSError, EnumerationError, exceptions.PysaurusError)):
            dialog = ft.AlertDialog(
                title=ft.Text(
                    f"Error: {' '.join(string_to_pieces(type(exception).__name__))}"
                ),
                content=ft.Text(str(exception)),
            )
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
        else:
            print("[Unhandled exception]", ctx["message"], file=sys.stderr)
            traceback.print_exception(exception)
            self.exit_code = 1
            if self.page:
                self.page.window_close()
            # loop.stop()


def main():
    loop = asyncio.get_event_loop()
    with App() as app:
        loop.set_exception_handler(app.exception_handler)
        coroutine = ft.app_async(app.run)
        loop.run_until_complete(coroutine)
        exit_code = app.exit_code
        # ft.app(app.run)
    sys.exit(exit_code)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.NOTSET)
    main()
