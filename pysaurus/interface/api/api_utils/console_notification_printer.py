import sys

from pysaurus.core.job_notifications import (
    JobProgressDisplay,
    JobToDo,
    NotificationDisplay,
)
from pysaurus.core.notifications import Notification


class ConsoleJobProgress(JobProgressDisplay):
    __slots__ = ("shift",)

    def __init__(self, job_to_do: JobToDo):
        self.shift = 0
        super().__init__(job_to_do)

    def _progress(self, step: int):
        """Manual console progress bar.

        NB: We cannot use tqdm here, because:
        - tqdm object cannot be pickled across processes.
        - I don't know how to recreate a tqdm attached to previous bar
          (new tqdm object will automatically write on next line).
        """
        total = self.job_to_do.total
        length_bar = 30
        length_done = int(length_bar * step / total) if total else length_bar
        output = (
            f"|{'█' * length_done}{' ' * (length_bar - length_done)}| "
            f"{step}/{total} {self.job_to_do.title}"
        )
        sys.stdout.write(("\r" * self.shift) + output)
        self.shift = len(output)
        if step == total:
            sys.stdout.write("\r\n")


class ConsoleNotificationPrinter(NotificationDisplay):
    __slots__ = ("progressions", "profiles", "nb_notifications")

    def _display_notification(self, notification: Notification):
        print(notification)

    def _new_progress(self, job_to_do: JobToDo):
        return ConsoleJobProgress(job_to_do)
