import videre
from pysaurus.core.job_notifications import (
    JobProgressDisplay,
    JobToDo,
    NotificationDisplay,
)
from pysaurus.core.notifications import Notification


class VidereJobProgressDisplay(JobProgressDisplay):
    __slots__ = ()

    def _progress(self, step: int):
        pass

    def __repr__(self):
        return f"Progress: {self.title}: {self.current} / {self.total}"


class VidereNotificationDisplay(NotificationDisplay):
    __slots__ = ()

    def _display_notification(self, notification: Notification):
        pass

    def _new_progress(self, job_to_do: JobToDo) -> JobProgressDisplay:
        return VidereJobProgressDisplay(job_to_do)


class ProcessPage(videre.Column):
    __wprops__ = {}
    __slots__ = ("text", "view", "notification_display")

    def __init__(self, title: str):
        self.text = videre.Text("...")
        self.view = videre.Column([self.text])
        self.notification_display = VidereNotificationDisplay()
        super().__init__(
            [
                videre.Column(
                    [videre.Text(title, strong=True)],
                    horizontal_alignment=videre.Alignment.CENTER,
                ),
                videre.ScrollView(self.view, weight=1),
            ]
        )

    def on_notification(self, notification: Notification):
        self.notification_display.print(notification)
        self.view.controls = [
            videre.Text(str(n)) for n in self.notification_display.views
        ]
