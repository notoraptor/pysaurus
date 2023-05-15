import multiprocessing
from queue import Empty

from pysaurus.core import profiling
from pysaurus.core.job_notifications import ConsoleJobProgress, JobStep, JobToDo
from pysaurus.interface.api.parallel_notifier import ParallelNotifier


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


class UnusedParallelNotifier(ParallelNotifier):
    __slots__ = ("_prev_profiling_start", "progress")

    def __init__(self, mp_manager: multiprocessing.Manager):
        super().__init__(mp_manager)
        self._prev_profiling_start = SharedObject(mp_manager)
        self.progress = SharedObject(mp_manager)

    def _print(self, notification):
        # Unused
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
