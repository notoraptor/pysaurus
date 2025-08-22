from typing import Callable

from ovld import OvldMC

import videre
from pysaurus.core.job_notifications import JobProgressDisplay, NotificationCollector
from pysaurus.core.notifications import End, Notification


def _on_end(callback, end_notification):
    def wrapper(button):
        callback(end_notification)

    return wrapper


class ProcessPage(videre.Column, metaclass=OvldMC):
    __wprops__ = {}
    __slots__ = ("title", "callback", "text", "header", "view", "n_collector")

    def __init__(self, title: str, callback: Callable[[End], None] | None = None):
        self.title = title
        self.callback = callback
        self.text = videre.Text(f"{title} ...", strong=True)
        self.header = videre.Column(
            [self.text],
            expand_horizontal=False,
            horizontal_alignment=videre.Alignment.CENTER,
        )
        self.view = videre.Column(
            [videre.Text("...")], expand_horizontal=True, key="view"
        )
        self.n_collector = NotificationCollector()
        super().__init__(
            [
                self.header,
                videre.ScrollView(
                    self.view, wrap_horizontal=True, default_bottom=True, weight=1
                ),
            ]
        )

    def on_notification(self, notification: Notification):
        self.n_collector.collect(notification)
        self.view.controls = [self.display(n) for n in self.n_collector.views]

    def display(self, notification: Notification):
        return videre.Text(str(notification))

    def display(self, notification: End):
        if type(notification) is not End and self.callback is not None:
            self.header.controls = [
                videre.Button("Continue", on_click=_on_end(self.callback, notification))
            ]
        else:
            self.text.text = str(self.title)
        return videre.Text(str(notification), strong=True)

    def display(self, progress: JobProgressDisplay):
        step = progress.current / progress.total
        percent = round(step * 100)
        name = videre.Text(
            f"{progress.title} ({percent} %)", wrap=videre.TextWrap.WORD, weight=1
        )
        bar = videre.ProgressBar(step, weight=3)
        return videre.Row(
            [name, bar], vertical_alignment=videre.Alignment.CENTER, space=5
        )
