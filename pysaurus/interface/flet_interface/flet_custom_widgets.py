import flet as ft

from pysaurus.interface.flet_interface.page.videos_page_utils import Action


class Title1(ft.Text):
    def __init__(self, text: str):
        super().__init__(text, size=26, weight=ft.FontWeight.BOLD)


class Title2(ft.Text):
    def __init__(self, text: str):
        super().__init__(text, size=24, weight=ft.FontWeight.BOLD)


class FletActionMenu(ft.MenuItemButton):
    def __init__(self, action: Action):
        super().__init__(content=ft.Text(action.title), on_click=action.on_click)
