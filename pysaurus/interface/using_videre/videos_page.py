from ovld import OvldMC

import videre
from pysaurus.core import notifications
from pysaurus.core.classes import Selector
from pysaurus.core.profiling import Profiler
from pysaurus.interface.using_videre.backend import get_backend
from pysaurus.interface.using_videre.common import (
    FIELD_MAP,
    SEARCH_COND_TITLE,
    Uniconst,
    pretty_grouping,
    pretty_quote,
)
from pysaurus.interface.using_videre.pagination import Pagination
from pysaurus.interface.using_videre.video_view import VideoView
from pysaurus.interface.using_videre.videos_page_dialogs import (
    DialogEditDatabaseFolders,
    DialogRenameDatabase,
)
from pysaurus.interface.using_videre.videre_notifications import (
    RequestedDatabaseUpdate,
    RequestedHomePage,
    VideoSelected,
)
from pysaurus.video.database_context import DatabaseContext
from videre.core.pygame_utils import Surface
from videre.widgets.widget import Widget


class VideosPage(videre.Column, metaclass=OvldMC):
    __wprops__ = {}
    __slots__ = ("context", "status_bar", "_info_folders", "_info_selector")

    def __init__(self, context: DatabaseContext):
        self.context = context
        self.status_bar = videre.Text("Ready.")
        self._info_folders = videre.Text()
        self._info_selector = videre.Text("")
        super().__init__(self._build(), space=5)

    def _update_info_folders(self):
        self._info_folders.text = f"{len(self.context.folders)} folder(s)"

    def _update_info_selector(self):
        total = self.context.view.view_count
        selector = self.context.view.selector
        if selector is None:
            message = "No video selected"
        else:
            message = f"{selector.size_from(total)} / {total} video(s) selected"
        self._info_selector.text = message

    def _build(self) -> list[Widget]:
        context = self.context
        view = context.view
        selector = view.selector

        top_bar = videre.Row(
            [
                # Database info
                videre.Text("Database:"),
                videre.Text(context.name, strong=True),
                videre.Text("|"),
                self._info_folders,
                # Menus
                *self._get_menus(),
                videre.Container(weight=1),
                # Videos pagination
                Pagination(
                    context.view.nb_pages,
                    context.view.page_number,
                    on_change=self._change_page,
                ),
            ],
            space=10,
            vertical_alignment=videre.Alignment.CENTER,
        )

        center_border_color = videre.Colors.lightgray
        center_bar = videre.Container(
            videre.Row(
                [
                    # Filters
                    videre.Container(
                        self._render_filters(),
                        weight=1,
                        border=videre.Border(right=(1, center_border_color)),
                    ),
                    # Videos
                    videre.ScrollView(
                        videre.Column(
                            [
                                VideoView(
                                    video,
                                    i,
                                    selected=selector is not None
                                    and selector.contains(video.video_id),
                                )
                                for i, video in enumerate(context.view.result)
                            ]
                        ),
                        wrap_horizontal=True,
                        weight=4,
                    ),
                ],
                space=5,
            ),
            weight=1,
            border=videre.Border.all(1, center_border_color),
        )

        bottom_bar = videre.Row(
            [
                self.status_bar,
                videre.Container(weight=1),
                videre.Text(
                    f"{view.selection_count} videos | "
                    f"{view.selection_file_size} | "
                    f"{view.selection_duration}"
                ),
            ]
        )

        self._update_info_folders()
        return [top_bar, center_bar, bottom_bar]

    def _render_filters(self) -> Widget:
        color_none = videre.Colors.gray
        view = self.context.view
        self._update_info_selector()
        return videre.Column(
            [
                videre.Text("FILTER", strong=True, italic=False, underline=True),
                videre.Text("Sources", strong=True, italic=True),
                *[videre.Text(" ".join(source)) for source in view.sources],
                videre.Text("Grouping", strong=True),
                *[
                    videre.Text(pretty_grouping(view.grouping))
                    if view.grouping
                    else videre.Text("Ungrouped", italic=True, color=color_none)
                ],
                videre.Text("Search", strong=True),
                *(
                    [
                        videre.Text(f"Searched {SEARCH_COND_TITLE[view.search.cond]}:"),
                        videre.Text(pretty_quote(view.search.text)),
                    ]
                    if view.search
                    else [videre.Text("No search", italic=True, color=color_none)]
                ),
                videre.Text("Sorted by", strong=True),
                *[
                    videre.Text(
                        f"{FIELD_MAP.get_title(field)} "
                        f"{Uniconst.ARROW_DOWN if reverse else Uniconst.ARROW_UP}"
                    )
                    for field, reverse in view.get_video_sorting()
                ],
                videre.Text("Selection", strong=True),
                self._info_selector,
            ],
            horizontal_alignment=videre.Alignment.CENTER,
        )

    def _get_menus(self) -> list[videre.ContextButton]:
        menus = [
            videre.ContextButton(
                "Database ...",
                actions=[
                    ("Reload database ...", self._action_reload_database),
                    ("Rename database ...", self._action_rename_database),
                    ("Edit database folders ...", self._action_edit_database_folders),
                    ("Close database ...", self._action_close_database),
                    ("Delete database ...", self._action_delete_database),
                ],
            )
        ]
        actions_videos = (
            (
                [("Open random video", self._action_open_random_video)]
                if self._can_open_random_video()
                else []
            )
            + (
                [("Find similar videos ...", self._action_find_similar_videos)]
                if self.context.view.source_count
                else []
            )
            + (
                [("Confirm all unique moves ...", self._action_make_unique_moves)]
                if self.context.view.grouped_by_moves()
                else []
            )
            + (
                [("Play list", self._action_play_list)]
                if self.context.view.view_count
                else []
            )
        )
        if actions_videos:
            menus.append(videre.ContextButton("Videos ...", actions=actions_videos))
        menus.extend(
            [
                videre.ContextButton(
                    "Prpoerties ...",
                    actions=[
                        ("Manage properties", self._action_manage_properties),
                        (
                            "Put keywords into a property ...",
                            self._action_fill_with_keywords,
                        ),
                        (
                            "Convert values to lowercase for ...",
                            self._action_props_to_lowercase,
                        ),
                        (
                            "Convert values to uppercase for ...",
                            self._action_props_to_uppercase,
                        ),
                    ],
                ),
                videre.ContextButton(
                    "Options ...",
                    actions=[
                        ("Set page size ...", self._action_set_page_size),
                        (
                            "Confirm deletion for entries not found",
                            self._action_on_not_found_deletion,
                        ),
                    ],
                ),
            ]
        )
        return menus

    def _change_page(self, page_number: int):
        self._reload(page_number)

    def _reload(self, page_number: int = 0):
        selector = self.context.view.selector
        context = get_backend(self).get_python_backend(
            self.context.view.page_size, page_number, None
        )
        context.view.selector = selector
        self.context = context
        self.controls = self._build()

    def on_notification(self, notification: notifications.Notification):
        pass

    def on_notification(self, notification: notifications.Message):
        self.status_bar.text = notification.message

    def on_notification(self, notification: VideoSelected):
        view = self.context.view
        selector = self.context.view.selector
        if selector:
            if notification.selected:
                selector.include(notification.video_id)
            elif selector.contains(notification.video_id):
                selector.exclude(notification.video_id)
        elif notification.selected:
            selector = Selector(False, {notification.video_id})
        if selector and not selector.size_from(view.view_count):
            selector = None
        self.context.view.selector = selector
        print("selector:", selector)
        self._update_info_selector()

    def _can_open_random_video(self) -> bool:
        # If any source contains "not_found", we may have videos not found,
        # so we won't try to open random video.
        for source in self.context.view.sources:
            if "not_found" in source:
                return False
        # Otherwise, we must have videos based on sources:
        return bool(self.context.view.source_count)

    def _action_reload_database(self):
        self.get_window().confirm(
            f"Do you want to reload database [{self.context.name}] now?",
            title="Reload database",
            on_confirm=self._on_reload_database,
        )

    def _on_reload_database(self):
        self.get_window().notify(RequestedDatabaseUpdate())

    def _action_rename_database(self):
        dialog = DialogRenameDatabase(self.context.name)
        button = videre.FancyCloseButton(
            "Rename database", on_click=self._on_rename_database, data=dialog
        )
        self.get_window().set_fancybox(
            dialog, title="Rename Database", buttons=[button]
        )

    def _on_rename_database(self, widget: Widget):
        dialog: DialogRenameDatabase = widget.data
        new_name = dialog.get_value()
        print("New database name:", new_name)
        get_backend(self).rename_database(new_name)
        self._reload()

    def _action_edit_database_folders(self):
        paths = self.context.folders
        dialog = DialogEditDatabaseFolders(
            paths,
            title=(
                f"Edit {len(self.context.folders)} initial folders"
                f" for database: {self.context.name}"
            ),
        )
        button = videre.FancyCloseButton(
            "edit folders", on_click=self._on_edit_database_folders, data=dialog
        )
        self.get_window().set_fancybox(
            dialog, title="Edit Database Folders", buttons=[button]
        )

    def _on_edit_database_folders(self, widget: Widget):
        dialog: DialogEditDatabaseFolders = widget.data
        paths = dialog.get_paths()
        backend = get_backend(self)
        backend.set_video_folders(paths)
        self.context.folders = paths
        self._update_info_folders()

    def _action_close_database(self):
        self.get_window().confirm(
            f"Do you want to close database [{self.context.name}] now?",
            title="Close database",
            on_confirm=self._on_close_database,
        )

    def _on_close_database(self):
        get_backend(self).close_database()
        self.get_window().notify(RequestedHomePage())

    def _action_delete_database(self):
        # todo
        pass

    def _action_open_random_video(self):
        path = get_backend(self).open_random_video()
        self.status_bar.text = f"Randomly opened: {path}"
        self._reload()

    def _action_find_similar_videos(self):
        # todo
        pass

    def _action_make_unique_moves(self):
        # todo
        pass

    def _action_play_list(self):
        # todo
        pass

    def _action_manage_properties(self):
        # todo
        pass

    def _action_fill_with_keywords(self):
        # todo
        pass

    def _action_props_to_lowercase(self):
        # todo
        pass

    def _action_props_to_uppercase(self):
        # todo
        pass

    def _action_set_page_size(self):
        # todo
        pass

    def _action_on_not_found_deletion(self):
        # todo
        pass

    @Profiler.profile("videos_page")
    def draw(self, window, width: int = None, height: int = None) -> Surface:
        return super().draw(window, width, height)
