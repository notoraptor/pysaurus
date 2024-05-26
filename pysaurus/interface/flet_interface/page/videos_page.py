from typing import Sequence

import flet as ft

from pysaurus.core.classes import Selector
from pysaurus.core.constants import (
    PAGE_SIZES,
    VIDEO_DEFAULT_PAGE_NUMBER,
    VIDEO_DEFAULT_PAGE_SIZE,
)
from pysaurus.interface.flet_interface.flet_custom_component.video_view import VideoView
from pysaurus.interface.flet_interface.flet_custom_widgets import FletActionMenu, Title2
from pysaurus.interface.flet_interface.flet_utils import FletUtils
from pysaurus.interface.flet_interface.page.videos_page_utils import (
    Action,
    Actions,
    StateWrapper,
)


class EventCallback:
    def __init__(self, function: callable, *arguments: Sequence):
        self.function = function
        self.arguments = arguments

    def __call__(self, e: ft.ControlEvent):
        self.function(*self.arguments)


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


class VideosPage(ft.Container):
    def __init__(self):
        super().__init__(LoadingView("Loading videos ..."))
        actions = [
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
                "sort", "Ctrl+S", "Sort ...", self.sortVideos, self._dialog_is_inactive
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
                "Play list",
                self.playlist,
                self._dialog_is_inactive,
            ),
        ]
        self.actions = Actions(actions)
        self.selector = Selector(exclude=False, selection=set())

    def did_mount(self):
        # Will load view and install global shortcuts
        self.page.run_task(self._load_videos)

    def will_unmount(self):
        # Uninstall global shortcuts
        interface = FletUtils.get_app_interface(self)
        interface.keyboard_callback = None

    async def _load_videos(self):
        interface = FletUtils.get_app_interface(self)
        state = StateWrapper(
            interface.backend(VIDEO_DEFAULT_PAGE_SIZE, VIDEO_DEFAULT_PAGE_NUMBER)
        )
        nb_folders = len(state.database.folders)
        search = state.search_def

        prop_types = state.prop_types
        string_properties = [desc for desc in prop_types if desc.type is str]
        string_set_properties = [desc for desc in string_properties if desc.multiple]

        menu = [
            ft.SubmenuButton(
                ft.Text("Database ..."),
                [
                    FletActionMenu(self.actions["reload"]),
                    ft.MenuItemButton(
                        ft.Text(f'Rename database "{state.database.name}" ...'),
                        on_click=self.on_rename_database,
                    ),
                    ft.MenuItemButton(
                        ft.Text(f"Edit {nb_folders} database folders ..."),
                        on_click=self.on_edit_database_folders,
                    ),
                    ft.MenuItemButton(
                        ft.Text("Close database ..."), on_click=self.on_close_database
                    ),
                    ft.MenuItemButton(
                        ft.Text("Delete database ..."), on_click=self.on_delete_database
                    ),
                ],
            ),
            ft.SubmenuButton(
                ft.Text("Videos ..."),
                [
                    ft.SubmenuButton(
                        ft.Text("Filter videos ..."),
                        [
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
                                [
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
                                        [FletActionMenu(self.actions["unsearch"])]
                                        if state.search_is_set()
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
                    ft.MenuItemButton(
                        ft.Text("Search similar videos"),
                        on_click=self.on_find_similar_videos,
                    ),
                    ft.MenuItemButton(
                        ft.Text("Search similar videos (ignore cache) ..."),
                        on_click=self.on_find_similar_videos_ignore_cache,
                    ),
                    *(
                        [
                            ft.MenuItemButton(
                                ft.Text("Confirm all unique moves ..."),
                                on_click=self.on_confirm_all_unique_moves,
                            )
                        ]
                        if state.is_grouped_by_moves()
                        else []
                    ),
                    FletActionMenu(self.actions["playlist"]),
                ],
            ),
            ft.SubmenuButton(
                ft.Text("Properties ..."),
                [
                    FletActionMenu(self.actions["manageProperties"]),
                    *(
                        [
                            ft.MenuItemButton(
                                ft.Text("Put keywords into a property ..."),
                                on_click=self.on_fill_with_keywords,
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
                                    ft.MenuItemButton(
                                        ft.Text(desc.name),
                                        data=desc.name,
                                        on_click=self.on_group_by_property,
                                    )
                                    for desc in prop_types
                                ],
                            )
                        ]
                        if len(prop_types) > 5
                        else [
                            ft.MenuItemButton(
                                ft.Text(f"Group videos by property: {desc.name}"),
                                data=desc.name,
                                on_click=self.on_group_by_property,
                            )
                            for desc in prop_types
                        ]
                    ),
                    *(
                        [
                            ft.SubmenuButton(
                                ft.Text("Convert values to lowercase for ..."),
                                [
                                    ft.MenuItemButton(
                                        ft.Text(desc.name),
                                        data=desc.name,
                                        on_click=self.on_prop_to_lowercase,
                                    )
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
                                    ft.MenuItemButton(
                                        ft.Text(desc.name),
                                        data=desc.name,
                                        on_click=self.on_prop_to_uppercase,
                                    )
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
                                        ft.Text("Go to previous group"),
                                        on_click=self.on_previous_group,
                                    ),
                                    ft.MenuItemButton(
                                        ft.Text("Go to next group"),
                                        on_click=self.on_next_group,
                                    ),
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
                    ft.RadioGroup(
                        ft.SubmenuButton(
                            ft.Text("Page size ..."),
                            [
                                ft.MenuItemButton(
                                    ft.Radio(
                                        value=count, label=f"{count} video(s) per page"
                                    ),
                                    style=ft.ButtonStyle(color=ft.colors.BLACK),
                                )
                                for count in PAGE_SIZES
                            ],
                        ),
                        value=PAGE_SIZES[-1],
                        on_change=self.on_set_page_size,
                    ),
                    ft.MenuItemButton(
                        ft.Text("confirm deletion for entries not found"),
                        on_click=self.on_confirm_deletion_for_entries_not_found,
                    ),
                ],
            ),
        ]
        menubar = ft.MenuBar(
            menu, expand=0, style=ft.MenuStyle(alignment=ft.alignment.top_left)
        )
        pagination = ft.Row(
            [
                ft.ElevatedButton(
                    "<<",
                    on_click=EventCallback(self.firstPage),
                    disabled=state.page_number == 0,
                ),
                ft.ElevatedButton(
                    "<",
                    on_click=EventCallback(self.previousPage),
                    disabled=state.page_number == 0,
                ),
                ft.Text(f"Page {state.page_number + 1} / {state.nb_pages}"),
                ft.ElevatedButton(
                    ">",
                    on_click=EventCallback(self.nextPage),
                    disabled=state.page_number == state.nb_pages - 1,
                ),
                ft.ElevatedButton(
                    ">>",
                    on_click=EventCallback(self.lastPage),
                    disabled=state.page_number == state.nb_pages - 1,
                ),
            ]
        )
        filter_view = ft.Column(
            [
                # sources
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    " ".join(flag.replace("_", " ") for flag in source)
                                )
                                for source in state.sources
                            ],
                            expand=1,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.IconButton(ft.icons.SETTINGS),
                                *(
                                    [ft.IconButton(ft.icons.CANCEL)]
                                    if state.source_is_set()
                                    else []
                                ),
                            ]
                        ),
                    ]
                ),
                # groups
                ft.Row(
                    [
                        ft.Column(
                            [
                                (
                                    ft.Text("Grouped")
                                    if state.group_is_set()
                                    else ft.Text(
                                        "Ungrouped", italic=True, color=ft.colors.GREY
                                    )
                                )
                            ],
                            expand=1,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.IconButton(ft.icons.SETTINGS),
                                *(
                                    [ft.IconButton(ft.icons.CANCEL)]
                                    if state.group_is_set()
                                    else []
                                ),
                            ]
                        ),
                    ]
                ),
                # search
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(f"Searched {search['cond']}"),
                                ft.Text(search["text"], weight=ft.FontWeight.BOLD),
                            ]
                            if state.group_is_set()
                            else [
                                ft.Text("No search", italic=True, color=ft.colors.GREY)
                            ],
                            expand=1,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.IconButton(ft.icons.SETTINGS),
                                *(
                                    [ft.IconButton(ft.icons.CANCEL)]
                                    if state.search_is_set()
                                    else []
                                ),
                            ]
                        ),
                    ]
                ),
                # sort
                ft.Row(
                    [
                        ft.Column(
                            [ft.Text("Sorted by")]
                            + [
                                ft.Text(
                                    criterion[1:]
                                    + " "
                                    + ("▼" if criterion[0] == "-" else "▲")
                                )
                                for criterion in state.sorting
                            ],
                            expand=1,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.IconButton(ft.icons.SETTINGS),
                                *(
                                    [ft.IconButton(ft.icons.CANCEL)]
                                    if state.sort_is_set()
                                    else []
                                ),
                            ]
                        ),
                    ]
                ),
                # selection
            ]
        )
        classifier_view = None
        group_view = None
        video_view = [
            VideoView(
                v,
                prop_types,
                i,
                common_fields=state.common_fields(),
                grouped_by_similarity=state.is_grouped_by_similarity(),
                is_selected=self.selector.contains(v.video_id),
                on_select=self.video_select,
            )
            for i, v in enumerate(state.videos)
        ]
        status_bar = ft.Row(
            [
                ft.Text("Ready."),
                ft.Text(
                    f"{state.nb_videos} video{'s' if state.nb_videos > 1 else ''} | "
                    f"{state.valid_size} | {state.valid_length}"
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Install global shortcuts
        interface.keyboard_callback = self.actions.on_keyboard_event

        self.content = ft.Column(
            [
                ft.Container(
                    ft.Row(
                        [menubar, pagination],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                ),
                ft.Row(
                    [
                        # left panel, filters and groups
                        ft.Container(filter_view, expand=15, bgcolor=ft.colors.RED),
                        # right panel, videos
                        ft.Container(
                            ft.Column(video_view, scroll=ft.ScrollMode.AUTO, spacing=0),
                            expand=85,
                            border_radius=10,
                            border=ft.border.all(1, ft.colors.GREY),
                        ),
                    ],
                    expand=1,
                ),
                ft.Container(
                    status_bar,
                    border=ft.border.only(top=ft.border.BorderSide(1, ft.colors.GREY)),
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
        )
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

    def firstPage(self):
        print("first page")

    def lastPage(self):
        print("last page")

    def playlist(self):
        print("from shortcut: playlist")

    def on_rename_database(self, e: ft.ControlEvent):
        print("on_rename_database")

    def on_edit_database_folders(self, e: ft.ControlEvent):
        print("on_edit_database_folders")

    def on_close_database(self, e: ft.ControlEvent):
        print("on_close_database")

    def on_delete_database(self, e: ft.ControlEvent):
        print("on_delete_database")

    def on_find_similar_videos(self, e: ft.ControlEvent):
        print("on_find_similar_videos")

    def on_find_similar_videos_ignore_cache(self, e: ft.ControlEvent):
        print("on_find_similar_videos_ignore_cache")

    def on_confirm_all_unique_moves(self, e: ft.ControlEvent):
        print("on_confirm_all_unique_moves")

    def on_group_by_property(self, e: ft.ControlEvent):
        print("on_group_by_property")

    def on_prop_to_lowercase(self, e: ft.ControlEvent):
        print("on_prop_to_lowercase")

    def on_prop_to_uppercase(self, e: ft.ControlEvent):
        print("on_prop_to_uppercase")

    def on_previous_group(self, e: ft.ControlEvent):
        print("on_previous_group")

    def on_next_group(self, e: ft.ControlEvent):
        print("on_next_group")

    def on_set_page_size(self, e: ft.ControlEvent):
        print("on_set_page_size")

    def on_confirm_deletion_for_entries_not_found(self, e: ft.ControlEvent):
        print("on_confirm_deletion_for_entries_not_found")

    def on_fill_with_keywords(self, e: ft.ControlEvent):
        print("on_fill_with_keywords")

    def canOpenRandomVideo(self) -> bool:
        return True

    def _dialog_is_inactive(self) -> bool:
        return self.page.dialog is None

    def video_select(self, video_id: int, is_selected: bool):
        if is_selected:
            self.selector.include(video_id)
        else:
            self.selector.exclude(video_id)
        print(self.selector)
