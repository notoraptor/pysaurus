"""Process page — progress display for long backend operations.

Transient screen created by ``VideroidApp.run_process``. Shows a spinner, a
bounded **jobs** zone (one progress bar per job) kept SEPARATE from a scrolling
**activity log** (with a Clear button), then enables the Continue button once the
operation ends (an :class:`End` notification, e.g. ``DatabaseReady``).
``autocontinue`` skips the button and proceeds immediately (kyuti does this when
opening a database without updating it).

Reference: kyuti/pages/process_page.py. videre gaps: no circular spinner
(``Progressing`` is an animated bar, ~G14); Continue can't be styled green
(G19); ``ProgressBar`` isn't stylable either.
"""

from __future__ import annotations

from typing import Callable

import videre
from videre.widgets.widget import Widget

from pysaurus.core.job_notifications import JobProgressDisplay, NotificationCollector
from pysaurus.core.notifications import End, Message, Notification


class ProcessPage:
    def __init__(
        self, title: str, on_end: Callable[[End], None], autocontinue: bool = False
    ):
        self._title = title
        self._on_end = on_end
        self._autocontinue = autocontinue
        self._collector = NotificationCollector()
        self._end: End | None = None
        self._log_hidden = 0  # number of log entries hidden by Clear

        self._title_text = videre.Text(f"{title} ...", strong=True, size=18)
        # Spinner in a holder so it can be hidden once the operation ends.
        self._spinner_holder = videre.Container(
            videre.Progressing(), horizontal_alignment=videre.Alignment.CENTER
        )
        self._jobs = videre.Column([], expand_horizontal=True, space=4)
        self._log = videre.Column([], expand_horizontal=True, space=2)
        # Present from the start but disabled until the op ends (kyuti). Styling
        # it green-when-enabled is a videre gap (G19: Button not stylable).
        self._continue = videre.Button(
            "Continue", on_click=self._on_continue, disabled=True
        )
        self._widget = videre.Column(
            [
                videre.Container(
                    self._title_text,
                    horizontal_alignment=videre.Alignment.CENTER,
                    padding=videre.Padding.all(6),
                ),
                self._spinner_holder,
                # Jobs zone: bounded height, framed (kyuti's jobs QScrollArea).
                videre.Container(
                    videre.ScrollView(self._jobs, wrap_horizontal=True),
                    height=180,
                    border=videre.Border.all(1, videre.Colors.lightgray),
                    padding=videre.Padding.all(4),
                ),
                videre.Row(
                    [
                        videre.Text("Activity Log:", strong=True, weight=1),
                        videre.Button("Clear", on_click=self._clear_log),
                    ],
                    vertical_alignment=videre.Alignment.CENTER,
                ),
                # Log zone: scrolls, takes the remaining space.
                videre.ScrollView(
                    self._log, wrap_horizontal=True, default_bottom=True, weight=1
                ),
                videre.Container(
                    self._continue,
                    horizontal_alignment=videre.Alignment.CENTER,
                    padding=videre.Padding.all(6),
                ),
            ],
            weight=1,
        )
        self._refresh()

    def get_widget(self) -> Widget:
        return self._widget

    def on_notification(self, notification: Notification) -> None:
        self._collector.collect(notification)
        self._refresh()
        if isinstance(notification, End):
            self._finish(notification)

    def _refresh(self) -> None:
        # `collector.views` is a flat, mixed list: JobProgressDisplay entries
        # (progress bars) interleaved with raw notifications (log lines).
        views = self._collector.views
        self._jobs.controls = [
            self._job_row(view)
            for view in views
            if isinstance(view, JobProgressDisplay)
        ] or [videre.Text("(no active job)", italic=True)]
        log_views = [v for v in views if not isinstance(v, JobProgressDisplay)]
        self._log.controls = [
            self._log_row(view) for view in log_views[self._log_hidden :]
        ] or [videre.Text("...")]

    def _job_row(self, view: JobProgressDisplay) -> Widget:
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

    def _log_row(self, view) -> Widget:
        if isinstance(view, End):
            return videre.Text(str(view), strong=True)
        if isinstance(view, Message):
            return videre.Text(view.message)
        return videre.Text(str(view))

    def _clear_log(self, widget: Widget) -> None:
        # Hide every log line seen so far; new ones will still appear. Jobs are
        # untouched (they live in a separate list).
        log_views = [
            v for v in self._collector.views if not isinstance(v, JobProgressDisplay)
        ]
        self._log_hidden = len(log_views)
        self._refresh()

    def _finish(self, end: End) -> None:
        self._end = end
        self._title_text.text = self._title
        self._spinner_holder.control = None  # stop showing the spinner
        if self._autocontinue:
            self._on_continue(None)
        else:
            self._continue.disabled = False

    def _on_continue(self, widget: Widget) -> None:
        self._on_end(self._end)
