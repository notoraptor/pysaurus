import flet as ft

from pysaurus.interface.flet_interface.flet_custom_widgets import FletActionMenu, Title2
from pysaurus.interface.flet_interface.flet_utils import FletUtils
from pysaurus.interface.flet_interface.page.videos_page_utils import (
    Action,
    Actions,
    PAGE_SIZES,
    StateWrapper,
    VIDEO_DEFAULT_PAGE_NUMBER,
    VIDEO_DEFAULT_PAGE_SIZE,
)


class VideosPage(ft.Column):
    def __init__(self):
        super().__init__(
            [
                ft.Row([ft.ProgressRing()], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row(
                    [Title2("Loading videos ...")],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.actions = Actions(
            [
                Action(
                    "select",
                    "Ctrl+T",
                    "Select videos ...",
                    self.selectVideos,
                    self._dialog_is_inactive,
                ),
                Action(
                    "group",
                    "Ctrl+G",
                    "Group ...",
                    self.groupVideos,
                    self._dialog_is_inactive,
                ),
                Action(
                    "search",
                    "Ctrl+F",
                    "Search ...",
                    self.searchVideos,
                    self._dialog_is_inactive,
                ),
                Action(
                    "sort",
                    "Ctrl+S",
                    "Sort ...",
                    self.sortVideos,
                    self._dialog_is_inactive,
                ),
                Action(
                    "unselect",
                    "Ctrl+Shift+T",
                    "Reset selection",
                    self.unselectVideos,
                    self._dialog_is_inactive,
                ),
                Action(
                    "ungroup",
                    "Ctrl+Shift+G",
                    "Reset group",
                    self.resetGroup,
                    self._dialog_is_inactive,
                ),
                Action(
                    "unsearch",
                    "Ctrl+Shift+F",
                    "Reset search",
                    self.resetSearch,
                    self._dialog_is_inactive,
                ),
                Action(
                    "unsort",
                    "Ctrl+Shift+S",
                    "Reset sorting",
                    self.resetSort,
                    self._dialog_is_inactive,
                ),
                Action(
                    "reload",
                    "Ctrl+R",
                    "Reload database ...",
                    self.reloadDatabase,
                    self._dialog_is_inactive,
                ),
                Action(
                    "manageProperties",
                    "Ctrl+P",
                    "Manage properties ...",
                    self.manageProperties,
                    self._dialog_is_inactive,
                ),
                Action(
                    "openRandomVideo",
                    "Ctrl+O",
                    "Open random video",
                    self.openRandomVideo,
                    self.canOpenRandomVideo,
                ),
                Action(
                    "previousPage",
                    "Ctrl+Arrow Left",
                    "Go to previous page",
                    self.previousPage,
                    self._dialog_is_inactive,
                ),
                Action(
                    "nextPage",
                    "Ctrl+Arrow Right",
                    "Go to next page",
                    self.nextPage,
                    self._dialog_is_inactive,
                ),
                Action(
                    "playlist",
                    "Ctrl+L",
                    "play list",
                    self.playlist,
                    self._dialog_is_inactive,
                ),
            ]
        )

    def did_mount(self):
        # Will load view and install global shortcuts
        self.page.run_task(self.load_videos)

    def will_unmount(self):
        # Uninstall global shortcuts
        interface = FletUtils.get_app_interface(self)
        interface.keyboard_callback = None

    async def load_videos(self):
        interface = FletUtils.get_app_interface(self)
        state = StateWrapper(
            interface.backend(VIDEO_DEFAULT_PAGE_SIZE, VIDEO_DEFAULT_PAGE_NUMBER)
        )
        nb_folders = len(state.database.folders)

        prop_types = state.prop_types
        string_properties = [desc for desc in prop_types if desc.type is str]
        string_set_properties = [desc for desc in string_properties if desc.multiple]

        menubar = ft.MenuBar(
            expand=0,
            style=ft.MenuStyle(alignment=ft.alignment.top_left),
            controls=[
                ft.SubmenuButton(
                    content=ft.Text("Database ..."),
                    controls=[
                        ft.MenuItemButton(ft.Text("Reload database ...")),
                        ft.MenuItemButton(
                            ft.Text(f'Rename database "{state.database.name}" ...')
                        ),
                        ft.MenuItemButton(
                            ft.Text(f"Edit {nb_folders} database folders ...")
                        ),
                        ft.MenuItemButton(ft.Text("Close database ...")),
                        ft.MenuItemButton(ft.Text("Delete database ...")),
                    ],
                ),
                ft.SubmenuButton(
                    content=ft.Text("Videos ..."),
                    controls=[
                        ft.SubmenuButton(
                            ft.Text("Filter videos ..."),
                            controls=[
                                FletActionMenu(self.actions["select"]),
                                FletActionMenu(self.actions["group"]),
                                FletActionMenu(self.actions["search"]),
                                FletActionMenu(self.actions["sort"]),
                            ],
                        ),
                        *(
                            [
                                ft.SubmenuButton(
                                    ft.Text("Reset filters ..."),
                                    controls=[
                                        *(
                                            [FletActionMenu(self.actions["unselect"])]
                                            if state.source_is_set()
                                            else []
                                        ),
                                        *(
                                            [FletActionMenu(self.actions["ungroup"])]
                                            if state.group_is_set()
                                            else []
                                        ),
                                        *(
                                            [FletActionMenu(self.actions["unsort"])]
                                            if state.sort_is_set()
                                            else []
                                        ),
                                    ],
                                )
                            ]
                            if state.is_filtered()
                            else []
                        ),
                        *(
                            [FletActionMenu(self.actions["openRandomVideo"])]
                            if self.canOpenRandomVideo()
                            else []
                        ),
                        ft.MenuItemButton(ft.Text("Search similar videos")),
                        ft.MenuItemButton(
                            ft.Text("Search similar videos (ignore cache) ...")
                        ),
                        *(
                            [ft.MenuItemButton(ft.Text("Confirm all unique moves ..."))]
                            if state.is_grouped_by_moves()
                            else []
                        ),
                        ft.MenuItemButton(ft.Text("Play list")),
                    ],
                ),
                ft.SubmenuButton(
                    content=ft.Text("Properties ..."),
                    controls=[
                        FletActionMenu(self.actions["manageProperties"]),
                        *(
                            [
                                ft.MenuItemButton(
                                    ft.Text("Put keywords into a property ...")
                                )
                            ]
                            if string_set_properties
                            else []
                        ),
                        *(
                            [
                                ft.SubmenuButton(
                                    ft.Text("Group videos by property ..."),
                                    [
                                        ft.MenuItemButton(ft.Text(desc.name))
                                        for desc in prop_types
                                    ],
                                )
                            ]
                            if len(prop_types) > 5
                            else [
                                ft.MenuItemButton(
                                    ft.Text(f"Group videos by property: {desc.name}")
                                )
                                for desc in prop_types
                            ]
                        ),
                        *(
                            [
                                ft.SubmenuButton(
                                    ft.Text("Convert values to lowercase for ..."),
                                    [
                                        ft.MenuItemButton(ft.Text(desc.name))
                                        for desc in string_properties
                                    ],
                                )
                            ]
                            if string_properties
                            else []
                        ),
                        *(
                            [
                                ft.SubmenuButton(
                                    ft.Text("Convert values to uppercase for ..."),
                                    [
                                        ft.MenuItemButton(ft.Text(desc.name))
                                        for desc in string_properties
                                    ],
                                )
                            ]
                            if string_properties
                            else []
                        ),
                    ],
                ),
                ft.SubmenuButton(
                    ft.Text("Navigation ..."),
                    [
                        ft.SubmenuButton(
                            ft.Text("Videos ...."),
                            [
                                FletActionMenu(self.actions["previousPage"]),
                                FletActionMenu(self.actions["nextPage"]),
                            ],
                        ),
                        *(
                            [
                                ft.SubmenuButton(
                                    ft.Text("Group ..."),
                                    [
                                        ft.MenuItemButton(
                                            ft.Text("Go to previous group")
                                        ),
                                        ft.MenuItemButton(ft.Text("Go to next group")),
                                    ],
                                )
                            ]
                            if state.group_is_set()
                            else []
                        ),
                    ],
                ),
                ft.SubmenuButton(
                    ft.Text("Options ..."),
                    [
                        ft.SubmenuButton(
                            ft.Text("Page size ..."),
                            [
                                ft.MenuItemButton(ft.Text(f"{count} video(s) per page"))
                                for count in PAGE_SIZES
                            ],
                        ),
                        ft.MenuItemButton(
                            ft.Text("confirm deletion for entries not found")
                        ),
                    ],
                ),
            ],
        )

        # Install global shortcuts
        interface.keyboard_callback = self.actions.on_keyboard_event

        self.controls = [
            menubar,
            ft.Container(ft.Text(f"{len(state.videos)} video(s)"), expand=1),
        ]
        self.update()

    def selectVideos(self):
        print("from shortcut: select videos")

    def groupVideos(self):
        print("from shortcut: group videos")

    def searchVideos(self):
        print("from shortcut: search videos")

    def sortVideos(self):
        print("from shortcut: sort videos")

    def unselectVideos(self):
        print("from shortcut: unselect videos")

    def resetGroup(self):
        print("from shortcut: reset group")

    def resetSearch(self):
        print("from shortcut: reset search")

    def resetSort(self):
        print("from shortcut: reset sort")

    def reloadDatabase(self):
        print("from shortcut: reload database")

    def manageProperties(self):
        print("from shortcut: manage properties")

    def openRandomVideo(self):
        print("from shortcut: open random video")

    def previousPage(self):
        print("from shortcut: previous page")

    def nextPage(self):
        print("from shortcut: next page")

    def playlist(self):
        print("from shortcut: playlist")

    def canOpenRandomVideo(self) -> bool:
        return True

    def _dialog_is_inactive(self) -> bool:
        return self.page.dialog is None
