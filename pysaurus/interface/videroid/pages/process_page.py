"""Process page — progress display for long backend operations.

Transient screen created by ``VideroidApp.run_process``. It shows a spinner, the
per-job progress bars and the activity log fed by backend notifications
(aggregated by :class:`NotificationCollector`), then a Continue button once the
operation ends (an :class:`End` notification, e.g. ``DatabaseReady``).
"""

from __future__ import annotations

from typing import Callable

import videre
from videre.widgets.widget import Widget

from pysaurus.core.job_notifications import JobProgressDisplay, NotificationCollector
from pysaurus.core.notifications import End, Message, Notification


class ProcessPage:
    def __init__(self, title: str, on_end: Callable[[End], None]):
        self._title = title
        self._on_end = on_end
        self._collector = NotificationCollector()
        self._end: End | None = None

        self._title_text = videre.Text(f"{title} ...", strong=True, size=18)
        self._spinner = videre.Progressing()
        # Footer holds the spinner while running, then the Continue button.
        self._footer = videre.Column(
            [self._spinner], horizontal_alignment=videre.Alignment.CENTER
        )
        self._view = videre.Column([], expand_horizontal=True, space=4)
        self._widget = videre.Column(
            [
                videre.Container(
                    self._title_text,
                    horizontal_alignment=videre.Alignment.CENTER,
                    padding=videre.Padding.all(6),
                ),
                videre.ScrollView(
                    self._view, wrap_horizontal=True, default_bottom=True, weight=1
                ),
                videre.Container(
                    self._footer,
                    horizontal_alignment=videre.Alignment.CENTER,
                    padding=videre.Padding.all(6),
                ),
            ]
        )

    def get_widget(self) -> Widget:
        return self._widget

    def on_notification(self, notification: Notification) -> None:
        self._collector.collect(notification)
        self._refresh_view()
        if isinstance(notification, End):
            self._finish(notification)

    def _refresh_view(self) -> None:
        self._view.controls = [
            self._display(view) for view in self._collector.views
        ] or [videre.Text("...")]

    def _display(self, view) -> Widget:
        if isinstance(view, JobProgressDisplay):
            step = view.current / (view.total or 1)
            title = view.title or view.job_to_do.name
            return videre.Row(
                [
                    videre.Text(
                        f"{title} ({round(step * 100)} %)",
                        wrap=videre.TextWrap.WORD,
                        weight=1,
                    ),
                    videre.ProgressBar(step, weight=3),
                ],
                vertical_alignment=videre.Alignment.CENTER,
                space=5,
            )
        if isinstance(view, End):
            return videre.Text(str(view), strong=True)
        if isinstance(view, Message):
            return videre.Text(view.message)
        return videre.Text(str(view))

    def _finish(self, end: End) -> None:
        self._end = end
        self._title_text.text = self._title
        self._footer.controls = [videre.Button("Continue", on_click=self._on_continue)]

    def _on_continue(self, widget: Widget) -> None:
        self._on_end(self._end)
