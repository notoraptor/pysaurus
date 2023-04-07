import multiprocessing
import sys
from queue import Empty

from pysaurus.core import profiling
from pysaurus.core.job_notifications import JobStep, JobToDo
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


class Progress:
    __slots__ = "job_to_do", "channels", "shift"

    def __init__(self, job_to_do: JobToDo):
        self.job_to_do = job_to_do
        self.channels = {}
        self.shift = 0
        print(job_to_do)
        self._progress(0)

    @property
    def done(self):
        return self.job_to_do.total == sum(self.channels.values(), start=0)

    def _progress(self, step):
        """Manual console progress bar.

        NB: We cannot use tqdm here, because:
        - tqdm object cannot be pickled across processes.
        - I don't know how to recreate a tqdm attached to previous bar
          (new tqdm object will automatically write on next line).
        """
        total = self.job_to_do.total
        length_bar = 30
        length_done = int(length_bar * step / total)
        output = (
            f"|{'█' * length_done}{' ' * (length_bar - length_done)}| "
            f"{step}/{total} {self.job_to_do.title}"
        )
        sys.stdout.write(("\r" * self.shift) + output)
        self.shift = len(output)
        if step == total:
            sys.stdout.write("\r\n")

    def update(self, job_step: JobStep):
        assert self.job_to_do.name == job_step.name
        self.channels[job_step.channel] = job_step.step
        self._progress(sum(self.channels.values()))


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
                self.progress.set(Progress(notification))
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
        self._print(notification)
        self.queue.put_nowait(notification)
        self.local_queue.put_nowait(notification)
