from ovld import OvldBase

import videre
from pysaurus.core.job_notifications import (
    JobProgressDisplay,
    JobToDo,
    NotificationDisplay,
)
from pysaurus.core.notifications import End, Notification


class VidereJobProgressDisplay(JobProgressDisplay):
    __slots__ = ()

    def _progress(self, step: int):
        pass


class VidereNotificationDisplay(NotificationDisplay):
    __slots__ = ()

    def _display_notification(self, notification: Notification):
        pass

    def _new_progress(self, job_to_do: JobToDo) -> JobProgressDisplay:
        return VidereJobProgressDisplay(job_to_do)


class NotificationRenderer(OvldBase):
    def display(self, notification: Notification):
        return videre.Text(str(notification))

    def display(self, notification: End):
        return videre.Text(str(notification), strong=True)

    def display(self, progress: VidereJobProgressDisplay):
        step = progress.current / progress.total
        percent = round(step * 100)
        name = videre.Text(
            f"{progress.title} ({percent} %)", wrap=videre.TextWrap.WORD, weight=1
        )
        bar = videre.ProgressBar(step, weight=3)
        output = videre.Row(
            [name, bar], vertical_alignment=videre.Alignment.CENTER, space=5
        )
        return output


class ProcessPage(videre.Column):
    __wprops__ = {}
    __slots__ = ("text", "view", "notification_display", "renderer")

    def __init__(self, title: str):
        self.text = videre.Text("...")
        self.view = videre.Column([self.text], expand_horizontal=True, key="view")
        self.notification_display = VidereNotificationDisplay()
        self.renderer = NotificationRenderer()
        super().__init__(
            [
                videre.Column(
                    [videre.Text(title, strong=True)],
                    horizontal_alignment=videre.Alignment.CENTER,
                ),
                videre.ScrollView(
                    self.view, wrap_horizontal=True, default_bottom=True, weight=1
                ),
            ]
        )

    def on_notification(self, notification: Notification):
        self.notification_display.print(notification)
        self.view.controls = [
            self.renderer.display(n) for n in self.notification_display.views
        ]
