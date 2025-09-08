import videre
from ovld import OvldMC
from videre.core.pygame_utils import Surface
from videre.widgets.widget import Widget

from pysaurus.core import notifications
from pysaurus.core.profiling import Profiler
from pysaurus.interface.using_videre.backend import get_backend
from pysaurus.interface.using_videre.pagination import Pagination
from pysaurus.interface.using_videre.video_view import VideoView
from pysaurus.video.database_context import DatabaseContext


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
                [
                    (
                        "Confirm all unique moves ...",
                        self._action_make_unique_moves,
                    )
                ]
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
            menus.append(
                videre.ContextButton(
                    "Videos ...",
                    actions=actions_videos,
                )
            )
        return menus

    def _change_page(self, page_number: int):
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
        # todo
        pass

    def _action_rename_database(self):
        # todo
        pass

    def _action_edit_database_folders(self):
        # todo
        pass

    def _action_close_database(self):
        # todo
        pass

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

    @Profiler.profile("videos_page")
    def draw(self, window, width: int = None, height: int = None) -> Surface:
        return super().draw(window, width, height)
