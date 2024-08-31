from typing import Optional

from pysaurus.core.job_notifications import ConsoleJobProgress, JobStep, JobToDo
from pysaurus.core.notifications import ProfilingEnd, ProfilingStart


class ConsoleNotificationPrinter:
    __slots__ = ("_prev_profiling_start", "progress")

    def __init__(self):
        self._prev_profiling_start: Optional[ProfilingStart] = None
        self.progress: Optional[ConsoleJobProgress] = None

    def print(self, notification):
        prev_profiling_start = self._prev_profiling_start
        self._prev_profiling_start = None
        if isinstance(notification, ProfilingStart):
            if prev_profiling_start:
                print("!", prev_profiling_start)
            self._prev_profiling_start = notification
        elif isinstance(notification, ProfilingEnd):
            if prev_profiling_start:
                assert prev_profiling_start.name == notification.name
                print(f"Profiled({notification.name}, {notification.time})")
            else:
                print(notification)
        else:
            if prev_profiling_start:
                print("?", prev_profiling_start)

            if isinstance(notification, JobToDo):
                progress = self.progress
                assert not progress or progress.done
                self.progress = ConsoleJobProgress(notification)
            elif isinstance(notification, JobStep):
                self.progress.update(notification)
            else:
                print(notification)
