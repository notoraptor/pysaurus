from typing import List, Set

import flet as ft

from pysaurus.core.components import AbsolutePath
from pysaurus.core.constants import VIDEO_SUPPORTED_EXTENSIONS
from pysaurus.interface.flet_interface.flet_utils import Title1, Title2


class Homepage(ft.Column):
    def __init__(self, page: ft.Page, db_names: List[str]):
        self.new_paths: Set[AbsolutePath] = set()
        self.view_selected_paths = ft.ListView(expand=1)
        self.files_picker = ft.FilePicker(on_result=self.pick_file)
        self.folder_picker = ft.FilePicker(on_result=self.pick_folder)
        page.overlay.append(self.files_picker)
        page.overlay.append(self.folder_picker)
        controls = [
            ft.Row(
                [Title1("Welcome to Pysaurus")], alignment=ft.MainAxisAlignment.CENTER
            ),
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.ElevatedButton(
                                        content=Title2("Create a database")
                                    )
                                ],
                                expand=1,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Column(
                                [ft.ElevatedButton(content=Title2(f"Open a database"))],
                                expand=1,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.TextField(label="Database name ...", expand=1),
                            ft.Column(
                                [ft.Text(f"({len(db_names)} available)")],
                                expand=1,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Text("Database files and folders:", expand=1),
                                    ft.ElevatedButton(
                                        "Add files ...",
                                        icon=ft.icons.VIDEO_FILE,
                                        on_click=self.on_add_files,
                                    ),
                                    ft.ElevatedButton(
                                        "Add folder ...",
                                        icon=ft.icons.FOLDER_OPEN,
                                        on_click=self.on_add_folder,
                                    ),
                                ],
                                expand=1,
                            ),
                            ft.Row(
                                [ft.Checkbox("Update on load")],
                                alignment=ft.MainAxisAlignment.CENTER,
                                expand=1,
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                self.view_selected_paths,
                                expand=1,
                                border_radius=10,
                                border=ft.border.all(1, ft.colors.GREY),
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
                        expand=1,
                    ),
                ],
                expand=1,
            ),
        ]
        super().__init__(controls)

    def on_add_files(self, e):
        self.files_picker.pick_files(
            dialog_title="Add files ...",
            allow_multiple=True,
            allowed_extensions=sorted(VIDEO_SUPPORTED_EXTENSIONS),
        )

    def on_add_folder(self, e):
        self.folder_picker.get_directory_path(dialog_title="Add folder ...")

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
