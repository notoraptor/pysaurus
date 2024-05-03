import flet as ft

from pysaurus.interface.flet_interface.extended_flet_api_interface import (
    ExtendedFletApiInterface,
)


class FletUtils:
    @staticmethod
    def set_page(page: ft.Page, content: ft.Control):
        page.controls.clear()
        page.add(ft.Container(content, expand=True))

    @staticmethod
    def get_app_interface(control: ft.Control) -> ExtendedFletApiInterface:
        if isinstance(control, ft.Page):
            interface = control.data
        else:
            interface = control.page.data
        assert isinstance(interface, ExtendedFletApiInterface)
        return interface
