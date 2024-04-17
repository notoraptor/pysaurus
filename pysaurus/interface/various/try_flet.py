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
        self.view_selected_paths = ft.ListView(expand=1)
        files_picker = ft.FilePicker(on_result=self.pick_file)
        folder_picker = ft.FilePicker(on_result=self.pick_folder)
        page.overlay.append(files_picker)
        page.overlay.append(folder_picker)
        controls = [
            ft.Container(
                ft.Row(
                    [ft.Text("Welcome to Pysaurus")],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                bgcolor=ft.colors.GREEN,
                expand=0,
            ),
            ft.Container(
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("Create a database"),
                                ft.Container(
                                    ft.Row(
                                        [
                                            ft.Text("New database name:", expand=1),
                                            ft.TextField(expand=1),
                                        ]
                                    ),
                                    bgcolor=ft.colors.YELLOW,
                                ),
                                ft.Row(
                                    [
                                        ft.Text(
                                            "Database files and folders:", expand=1
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
                                                    "Add folder ...",
                                                    icon=ft.icons.FOLDER_OPEN,
                                                    on_click=lambda _: folder_picker.get_directory_path(
                                                        dialog_title="Add folder ..."
                                                    ),
                                                ),
                                            ],
                                            expand=1,
                                        ),
                                    ]
                                ),
                                ft.Container(
                                    self.view_selected_paths,
                                    bgcolor=ft.colors.PINK,
                                    expand=1,
                                    border_radius=10,
                                    border=ft.border.all(1, ft.colors.GREY),
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            expand=1,
                        ),
                        ft.Column(
                            [
                                ft.Text(f"Open a database ({len(db_names)} available)"),
                                ft.Row(
                                    [ft.Checkbox("Update on load")],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                ft.Container(
                                    ft.RadioGroup(
                                        ft.ListView(
                                            [
                                                ft.Radio(value=name, label=name)
                                                for name in db_names
                                            ]
                                        )
                                    ),
                                    expand=1,
                                    border_radius=10,
                                    border=ft.border.all(1, ft.colors.GREY),
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            expand=1,
                        ),
                    ]
                ),
                bgcolor=ft.colors.BLUE,
                expand=1,
            ),
            ft.Row(
                [
                    ft.Row(
                        [ft.TextButton("Create database")],
                        alignment=ft.MainAxisAlignment.CENTER,
                        expand=1,
                    ),
                    ft.Container(bgcolor=ft.colors.PURPLE, expand=1),
                ],
                expand=0,
            ),
        ]
        super().__init__(controls)

    def pick_file(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.new_paths.update(AbsolutePath(filename.path) for filename in e.files)
            self.render_new_paths()

    def pick_folder(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.new_paths.add(AbsolutePath(e.path))
            self.render_new_paths()

    def render_new_paths(self):
        self.view_selected_paths.controls.clear()
        for filename in sorted(self.new_paths):
            self.view_selected_paths.controls.append(
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.icons.DELETE,
                            on_click=self.on_remove_new_path,
                            data=filename,
                        ),
                        ft.Text(filename.standard_path),
                    ]
                )
            )
        self.view_selected_paths.update()

    def on_remove_new_path(self, e: ft.ControlEvent):
        path = e.control.data
        if path in self.new_paths:
            self.new_paths.remove(path)
            self.render_new_paths()


class App:
    def __init__(self):
        self.api = Api()

    def run(self, page: ft.Page):
        api = self.api
        db_names = api.__run_feature__("get_database_names")

        page.title = "Pysaurus"
        page.add(
            ft.Container(Homepage(page, db_names), bgcolor=ft.colors.RED, expand=True)
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.api.close_app()


if __name__ == "__main__":
    with App() as pysaurus_flet_app:
        ft.app(pysaurus_flet_app.run)
