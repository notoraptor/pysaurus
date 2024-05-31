import asyncio
import os
import sys
import traceback
from typing import Optional

import flet as ft

from pysaurus.application import exceptions
from pysaurus.core.enumeration import EnumerationError
from pysaurus.core.functions import string_to_pieces
from pysaurus.interface.flet_interface.extended_flet_api_interface import (
    ExtendedFletApiInterface,
)
from pysaurus.interface.flet_interface.flet_api_interface import FletApiInterface
from pysaurus.interface.flet_interface.flet_gui_api import FletGuiAPI
from pysaurus.interface.flet_interface.flet_utils import FletUtils
from pysaurus.interface.flet_interface.page.homepage import Homepage

_CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__))
_MONOSPACE_FONT = os.path.join(
    _CURRENT_FOLDER, "fonts", "Roboto_Mono", "RobotoMono-VariableFont_wght.ttf"
)
assert os.path.isfile(_MONOSPACE_FONT)


class App:
    __slots__ = ("interface", "page", "exit_code")

    def __init__(self):
        self.interface: Optional[FletApiInterface] = None
        self.page: Optional[ft.Page] = None
        self.exit_code = 1

    def run(self, page: ft.Page):
        page.window_center()

        self.page = page
        self.interface = ExtendedFletApiInterface(FletGuiAPI(page))
        db_names = self.interface.get_database_names()

        page.fonts = {"Roboto Mono": _MONOSPACE_FONT}
        page.data = self.interface
        page.title = "Pysaurus"
        page.on_keyboard_event = self.interface.on_keyboard
        FletUtils.set_page(page, Homepage(db_names))
        self.exit_code = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.interface:
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
        coroutine = ft.app_async(app.run, view=ft.AppView.FLET_APP_HIDDEN)
        loop.run_until_complete(coroutine)
        exit_code = app.exit_code
        # ft.app(app.run)
    sys.exit(exit_code)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    main()
