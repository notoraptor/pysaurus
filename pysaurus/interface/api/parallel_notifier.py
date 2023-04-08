import multiprocessing
from queue import Empty

from pysaurus.core import profiling
from pysaurus.core.job_notifications import ConsoleJobProgress, JobStep, JobToDo
from pysaurus.core.notifications import Notification
from pysaurus.core.notifying import Notifier


class SharedObject:
    __slots__ = ("__q",)

    def __init__(self, mp_manager: multiprocessing.Manager):
        self.__q = mp_manager.Queue()

    def set(self, value):
        self.__q.put_nowait(value)

    def get(self):
        values = []
        while True:
            try:
                values.append(self.__q.get_nowait())
            except Empty:
                break
        if values:
            (value,) = values
            return value
        else:
            return None


class ParallelNotifier(Notifier):
    __slots__ = ("queue", "local_queue", "_prev_profiling_start", "progress")

    def __init__(self, mp_manager: multiprocessing.Manager):
        super(ParallelNotifier, self).__init__()
        self.queue = mp_manager.Queue()
        self.local_queue = mp_manager.Queue()
        self._prev_profiling_start = SharedObject(mp_manager)
        self.progress = SharedObject(mp_manager)

    def _print(self, notification):
        prev_profiling_start = self._prev_profiling_start.get()
        if isinstance(notification, profiling.ProfilingStart):
            if prev_profiling_start:
                print("!", prev_profiling_start)
            self._prev_profiling_start.set(notification)
        elif isinstance(notification, profiling.ProfilingEnd):
            if prev_profiling_start:
                assert prev_profiling_start.name == notification.name
                print(f"Profiled({notification.name}, {notification.time})")
                self._prev_profiling_start.set(None)
            else:
                print(notification)
        else:
            if prev_profiling_start:
                print("?", prev_profiling_start)
                self._prev_profiling_start.set(None)

            if isinstance(notification, JobToDo):
                progress = self.progress.get()
                assert not progress or progress.done
                self.progress.set(ConsoleJobProgress(notification))
            elif isinstance(notification, JobStep):
                progress = self.progress.get()
                assert progress
                progress.update(notification)
                self.progress.set(progress)
            else:
                print(notification)

    def close(self):
        self.queue = None
        self.local_queue = None

    def manage(self, notification):
        # type: (Notification) -> None
        # print(notification)
        self.queue.put_nowait(notification)
        self.local_queue.put_nowait(notification)
