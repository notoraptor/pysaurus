import flet as ft


class Title1(ft.Text):
    def __init__(self, text: str):
        super().__init__(text, size=26, weight=ft.FontWeight.BOLD)


class Title2(ft.Text):
    def __init__(self, text: str):
        super().__init__(text, size=24, weight=ft.FontWeight.BOLD)


def set_page(page: ft.Page, content: ft.Control):
    page.controls.clear()
    page.add(ft.Container(content, expand=True))
