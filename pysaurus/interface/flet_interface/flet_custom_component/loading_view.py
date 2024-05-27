import flet as ft

from pysaurus.interface.flet_interface.flet_custom_widgets import Title2


class LoadingView(ft.Column):
    def __init__(self, title: str):
        super().__init__(
            [
                ft.Row([ft.ProgressRing()], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([Title2(title)], alignment=ft.MainAxisAlignment.CENTER),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
