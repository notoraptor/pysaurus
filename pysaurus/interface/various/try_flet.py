from typing import List, Set

import flet as ft

from pysaurus.core.components import AbsolutePath
from pysaurus.core.constants import VIDEO_SUPPORTED_EXTENSIONS
from pysaurus.core.notifications import Notification
from pysaurus.interface.api.gui_api import GuiAPI


class Api(GuiAPI):
    def _notify(self, notification: Notification) -> None:
        pass


class Homepage(ft.Column):
    def __init__(self, page: ft.Page, db_names: List[str]):
        self.new_paths: Set[AbsolutePath] = set()
        self.view_selected_paths = ft.Column()
        files_picker = ft.FilePicker(on_result=self.pick_file)
        folder_picker = ft.FilePicker(on_result=self.pick_folder)
        page.overlay.append(files_picker)
        page.overlay.append(folder_picker)
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
                                        ft.ElevatedButton(
                                            "Add files ...",
                                            icon=ft.icons.VIDEO_FILE,
                                            on_click=lambda _: files_picker.pick_files(
                                                dialog_title="Add files ...",
                                                allow_multiple=True,
                                                allowed_extensions=sorted(
                                                    VIDEO_SUPPORTED_EXTENSIONS
                                                ),
                                            ),
                                        ),
                                        ft.ElevatedButton(
                                            "Add a folder ...",
                                            icon=ft.icons.FOLDER_OPEN,
                                            on_click=lambda _: folder_picker.get_directory_path(
                                                dialog_title="Add folder ..."
                                            ),
                                        ),
                                    ]
                                ),
                                self.view_selected_paths,
                                ft.TextButton("Create database"),
                            ]
                        ),
                        ft.Column(
                            [
                                ft.Text(f"Open a database ({len(db_names)} available)"),
                                *[ft.TextButton(name) for name in db_names],
                            ]
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def pick_file(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.new_paths.update(AbsolutePath(filename.path) for filename in e.files)
            self._render_new_paths()

    def pick_folder(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.new_paths.add(AbsolutePath(e.path))
            self._render_new_paths()

    def remove_new_path(self, path: AbsolutePath):
        if path in self.new_paths:
            self.new_paths.remove(path)
            self._render_new_paths()

    def on_remove_path(self, e: ft.ControlEvent):
        path = e.control.data
        self.remove_new_path(path)

    def _render_new_paths(self):
        self.view_selected_paths.controls.clear()
        for filename in sorted(self.new_paths):
            self.view_selected_paths.controls.append(
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.icons.DELETE,
                            on_click=self.on_remove_path,
                            data=filename
                        ),
                        ft.Text(filename.standard_path),
                    ]
                )
            )
        self.view_selected_paths.update()


def main(page: ft.Page):
    api = Api()
    db_names = api.__run_feature__("get_database_names")

    page.title = "Pysaurus"
    # page.vertical_alignment = ft.MainAxisAlignment.CENTER
    # page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.add(Homepage(page, db_names))


if __name__ == "__main__":
    import asyncio

    # import logging
    # logging.basicConfig(level=logging.DEBUG)
    async_main = ft.app_async(main)
    asyncio.run(async_main)
