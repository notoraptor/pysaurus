from typing import List

import flet as ft

from pysaurus.core.notifications import Notification
from pysaurus.interface.api.gui_api import GuiAPI


class Api(GuiAPI):
    def _notify(self, notification: Notification) -> None:
        pass


class Homepage(ft.Column):
    def __init__(self, db_names: List[str]):
        super().__init__(
            [
                ft.Row(
                    [ft.Text("Welcome to Pysaurus")],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("Create a database"),
                                ft.Row([ft.Text("New database name:"), ft.TextField()]),
                                ft.Row(
                                    [ft.Text("Database files and folders:"), ft.Text()]
                                ),
                                ft.Row(
                                    [
                                        ft.TextButton("Add a file ..."),
                                        ft.TextButton("Add a folder ..."),
                                    ]
                                ),
                                ft.Column(),
                                ft.TextButton("Create database"),
                            ],
                        ),
                        ft.Column(
                            [
                                ft.Text(f"Open a database ({len(db_names)} available)"),
                                *[ft.TextButton(name) for name in db_names],
                            ],
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )


def main(page: ft.Page):
    api = Api()
    db_names = api.__run_feature__("get_database_names")

    page.title = "Pysaurus"
    # page.vertical_alignment = ft.MainAxisAlignment.CENTER
    # page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.add(Homepage(db_names))


if __name__ == "__main__":
    import asyncio

    # import logging
    # logging.basicConfig(level=logging.DEBUG)
    async_main = ft.app_async(main)
    asyncio.run(async_main)
