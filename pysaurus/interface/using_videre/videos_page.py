from collections.abc import Callable

import videre
from ovld import OvldMC
from typing_extensions import TypeAlias
from videre.core.pygame_utils import Surface
from videre.widgets.widget import Widget

from pysaurus.core import notifications
from pysaurus.core.profiling import Profiler
from pysaurus.interface.using_videre.backend import get_backend
from pysaurus.interface.using_videre.pagination import Pagination
from pysaurus.interface.using_videre.video_view import VideoView
from pysaurus.video.database_context import DatabaseContext

BackendUpdater: TypeAlias = Callable[[int, int, dict | None], DatabaseContext]


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

        database_title = videre.Text(f"Database: {context.name}")
        pagination = Pagination(
            context.view.nb_pages, context.view.page_number, on_change=self._change_page
        )
        top_bar = videre.Row([database_title, videre.Container(weight=1), pagination])
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

    @Profiler.profile("videos_page")
    def draw(self, window, width: int = None, height: int = None) -> Surface:
        return super().draw(window, width, height)
