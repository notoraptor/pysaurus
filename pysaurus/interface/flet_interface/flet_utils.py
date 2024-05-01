import flet as ft

from pysaurus.interface.flet_interface.flet_api_interface import FletApiInterface


class Title1(ft.Text):
    def __init__(self, text: str):
        super().__init__(text, size=26, weight=ft.FontWeight.BOLD)


class Title2(ft.Text):
    def __init__(self, text: str):
        super().__init__(text, size=24, weight=ft.FontWeight.BOLD)


class FletUtils:
    @staticmethod
    def set_page(page: ft.Page, content: ft.Control):
        page.controls.clear()
        page.add(ft.Container(content, expand=True))

    @staticmethod
    def get_app_interface(control: ft.Control) -> FletApiInterface:
        if isinstance(control, ft.Page):
            interface = control.data
        else:
            interface = control.page.data
        assert isinstance(interface, FletApiInterface)
        return interface
