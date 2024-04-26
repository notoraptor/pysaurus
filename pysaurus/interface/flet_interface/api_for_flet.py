import functools
import threading

import flet as ft

from pysaurus.core.notifications import Notification
from pysaurus.interface.api.gui_api import GuiAPI


def do_nothing():
    pass


def dummy_thread():
    th = threading.Thread(target=do_nothing)
    th.start()
    return th


class ApiForFlet(GuiAPI):

    def __init__(self, page: ft.Page):
        self.page = page
        super().__init__()

    def _run_thread(self, function, *args, **kwargs) -> threading.Thread:
        if kwargs:
            handler = functools.partial(function, **kwargs)
        else:
            handler = function
        print("Running", function)
        self.page.run_thread(handler, *args)
        return None

    def _notify(self, notification: Notification) -> None:
        print("Received", notification)
