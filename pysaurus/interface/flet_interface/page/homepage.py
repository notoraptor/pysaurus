from typing import List, Optional, Set

import flet as ft

from pysaurus.application import exceptions
from pysaurus.core.components import AbsolutePath
from pysaurus.core.constants import VIDEO_SUPPORTED_EXTENSIONS
from pysaurus.interface.flet_interface.flet_custom_widgets import Title1, Title2
from pysaurus.interface.flet_interface.flet_utils import FletUtils
from pysaurus.interface.flet_interface.page.taskpage import TaskPage


class Homepage(ft.Column):
    def __init__(self, page: ft.Page, db_names: List[str]):
        super().__init__()
        self.new_name: str = ""
        self.new_paths: Set[AbsolutePath] = set()
        self.database_to_load: Optional[str] = None
        self.update_on_load: bool = False

        self.new_paths_view = ft.ListView(expand=1)
        self.files_picker = ft.FilePicker(on_result=self.on_result_pick_files)
        self.folder_picker = ft.FilePicker(on_result=self.on_result_pick_folder)
        self.button_create_database = ft.ElevatedButton(
            content=Title2("Create a database"),
            on_click=self.on_create_database,
            disabled=True,
        )
        self.button_open_database = ft.ElevatedButton(
            content=Title2(f"Open a database"),
            on_click=self.on_open_database,
            disabled=True,
        )
        # self.page = page
        page.overlay.append(self.files_picker)
        page.overlay.append(self.folder_picker)
        self.controls = [
            ft.Row(
                [Title1("Welcome to Pysaurus")], alignment=ft.MainAxisAlignment.CENTER
            ),
            ft.Column(
                [
                    # Header
                    ft.Row(
                        [
                            ft.Column(
                                [self.button_create_database],
                                expand=1,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Column(
                                [self.button_open_database],
                                expand=1,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ]
                    ),
                    # Database name | Number of available databases
                    ft.Row(
                        [
                            ft.TextField(
                                label="Database name ...",
                                value=self.new_name,
                                on_change=self.on_change_new_name,
                                expand=1,
                            ),
                            ft.Column(
                                [ft.Text(f"({len(db_names)} available)")],
                                expand=1,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ]
                    ),
                    # Database files and folders | update on load
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
                                [
                                    ft.Checkbox(
                                        "Update on load",
                                        value=self.update_on_load,
                                        on_change=self.on_change_update,
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                expand=1,
                            ),
                        ]
                    ),
                    # New paths | Available databases
                    ft.Row(
                        [
                            ft.Container(
                                self.new_paths_view,
                                expand=1,
                                border_radius=10,
                                border=ft.border.all(1, ft.colors.GREY),
                            ),
                            ft.Container(
                                ft.RadioGroup(
                                    ft.ListView(
                                        [
                                            ft.Radio(
                                                value=name, label=name, toggleable=True
                                            )
                                            for name in db_names
                                        ]
                                    ),
                                    on_change=self.on_database_change,
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

    def on_result_pick_files(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.new_paths.update(AbsolutePath(filename.path) for filename in e.files)
            self.render_new_paths()

    def on_result_pick_folder(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.new_paths.add(AbsolutePath(e.path))
            self.render_new_paths()

    def render_new_paths(self):
        self.new_paths_view.controls.clear()
        for filename in sorted(self.new_paths):
            self.new_paths_view.controls.append(
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
        self.new_paths_view.update()

    def on_remove_new_path(self, e: ft.ControlEvent):
        path = e.control.data
        if path in self.new_paths:
            self.new_paths.remove(path)
            self.render_new_paths()

    def on_add_files(self, e):
        self.files_picker.pick_files(
            dialog_title="Add files ...",
            allow_multiple=True,
            allowed_extensions=sorted(VIDEO_SUPPORTED_EXTENSIONS),
        )

    def on_add_folder(self, e):
        self.folder_picker.get_directory_path(dialog_title="Add folder ...")

    def on_database_change(self, e):
        self.database_to_load = e.control.value
        self.button_open_database.disabled = not self.database_to_load
        self.button_open_database.update()

    def on_change_update(self, e):
        self.update_on_load = e.control.value

    def on_change_new_name(self, e):
        self.new_name = e.control.value
        self.button_create_database.disabled = not self.new_name.strip()
        self.button_create_database.update()

    def on_create_database(self, e):
        pass

    def on_open_database(self, e):
        if self.database_to_load:
            self.database_to_load = self.database_to_load.strip()
        if not self.database_to_load:
            raise exceptions.InvalidDatabaseName()
        print("Opening", self.database_to_load, "with loading ?", self.update_on_load)
        interface = FletUtils.get_app_interface(self)
        FletUtils.set_page(
            self.page,
            TaskPage(
                interface.open_database,
                (self.database_to_load, self.update_on_load),
                title=f"Open database 『{self.database_to_load}』",
            ),
        )
