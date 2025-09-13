import videre
from ovld import OvldMC
from videre.core.pygame_utils import Surface
from videre.widgets.widget import Widget

from pysaurus.core import notifications
from pysaurus.core.profiling import Profiler
from pysaurus.interface.using_videre.backend import get_backend
from pysaurus.interface.using_videre.pagination import Pagination
from pysaurus.interface.using_videre.video_view import VideoView
from pysaurus.interface.using_videre.videre_notifications import (
    RequestedDatabaseUpdate,
    RequestedHomePage,
)
from pysaurus.video.database_context import DatabaseContext


class DialogRenameDatabase(videre.Column):
    __wprops__ = {}
    __slots__ = ("_entry",)

    def __init__(self, old_name: str):
        self._entry = videre.TextInput(old_name)
        super().__init__(
            [
                videre.Text("Old name:"),
                videre.Text(old_name),
                videre.Text("New name:"),
                self._entry,
            ],
            horizontal_alignment=videre.Alignment.CENTER,
            expand_horizontal=True,
            space=10,
        )

    def get_value(self) -> str:
        return self._entry.value


class VideosPage(videre.Column, metaclass=OvldMC):
    __wprops__ = {}
    __slots__ = ("context", "status_bar")

    def __init__(self, context: DatabaseContext):
        self.context = context
        self.status_bar = videre.Text("Ready.")
        super().__init__(self._build())

    def _build(self) -> list[Widget]:
        context = self.context
        view = context.view

        videos_view = videre.Column(
            [VideoView(video, i) for i, video in enumerate(context.view.result)]
        )

        left_bar = videre.Text("view parameters", weight=1)
        right_view = videre.ScrollView(videos_view, wrap_horizontal=True, weight=4)

        menus = self._get_menus()
        pagination = Pagination(
            context.view.nb_pages, context.view.page_number, on_change=self._change_page
        )
        top_bar = videre.Row(
            [
                videre.Text("Database:"),
                videre.Text(context.name, strong=True),
                videre.Text("|"),
                videre.Text(f"{len(self.context.folders)} folder(s)"),
                *menus,
                videre.Container(weight=1),
                pagination,
            ],
            space=10,
            vertical_alignment=videre.Alignment.CENTER,
        )
        center_bar = videre.Row([left_bar, right_view], weight=1)
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

        return [top_bar, center_bar, bottom_bar]

    def _get_menus(self):
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
                    "Proerties ...",
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
        context = get_backend(self).get_python_backend(
            self.context.view.page_size, page_number, None
        )
        self.context = context
        self.controls = self._build()

    def on_notification(self, notification: notifications.Notification):
        pass

    def on_notification(self, notification: notifications.Message):
        self.status_bar.text = notification.message

    def _can_open_random_video(self):
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
        # todo
        pass

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
        # todo
        pass

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
