import flet as ft

from pysaurus.interface.api.gui_api import GuiAPI
from pysaurus.interface.flet_interface.flet_api_interface import FletApiInterface


class ExtendedFletApiInterface(FletApiInterface):
    __slots__ = ("keyboard_callback",)

    def __init__(self, api: GuiAPI):
        super().__init__(api)
        self.keyboard_callback = None

    def on_keyboard(self, e: ft.KeyboardEvent):
        if self.keyboard_callback:
            self.keyboard_callback(e)
