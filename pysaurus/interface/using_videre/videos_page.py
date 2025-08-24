from collections.abc import Callable

from ovld import OvldMC
from typing_extensions import TypeAlias

import videre
from pysaurus.core import notifications
from pysaurus.core.profiling import Profiler
from pysaurus.interface.using_videre.video_view import VideoView
from pysaurus.video.database_context import DatabaseContext
from videre.core.pygame_utils import Surface
from videre.widgets.widget import Widget


class Pagination(videre.Row):
    __wprops__ = {}
    __slots__ = ("_on_change", "_page_number", "_nb_pages")

    def __init__(
        self, nb_pages: int, page_number: int, on_change: Callable[[int], None]
    ):
        self._on_change = on_change
        self._page_number = page_number
        self._nb_pages = nb_pages
        b_start = videre.Button(
            "<<", on_click=self._on_first, disabled=page_number == 0
        )
        b_prev = videre.Button(
            "<", on_click=self._on_previous, disabled=page_number == 0
        )
        b_next = videre.Button(
            ">", on_click=self._on_next, disabled=page_number == nb_pages - 1
        )
        b_last = videre.Button(
            ">>", on_click=self._on_last, disabled=page_number == nb_pages - 1
        )
        info = videre.Text(f"Page {page_number + 1}/{nb_pages}")
        super().__init__([b_start, b_prev, info, b_next, b_last], space=10)

    def _on_first(self, *args):
        if self._page_number != 0:
            self._on_change(0)

    def _on_last(self, *args):
        if self._page_number != self._nb_pages - 1:
            self._on_change(self._nb_pages - 1)

    def _on_previous(self, *args):
        if self._page_number > 0:
            self._on_change(self._page_number - 1)

    def _on_next(self, *args):
        if self._page_number < self._nb_pages - 1:
            self._on_change(self._page_number + 1)


BackendUpdater: TypeAlias = Callable[[int, int, dict | None], DatabaseContext]


class VideosPage(videre.Column, metaclass=OvldMC):
    __wprops__ = {}
    __slots__ = ("context", "context_updater", "status_bar")

    def __init__(self, context: DatabaseContext, updater: BackendUpdater):
        self.context = context
        self.context_updater = updater
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
        context = self.context_updater(self.context.view.page_size, page_number, None)
        self.context = context
        self.controls = self._build()

    def on_notification(self, notification: notifications.Notification):
        pass

    def on_notification(self, notification: notifications.Message):
        self.status_bar.text = notification.message

    @Profiler.profile("videos_page")
    def draw(self, window, width: int = None, height: int = None) -> Surface:
        return super().draw(window, width, height)
