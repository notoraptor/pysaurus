import multiprocessing

from pysaurus.core.notifications import Notification
from pysaurus.core.notifying import Notifier


class ParallelNotifier(Notifier):
    __slots__ = ("queue", "local_queue")

    def __init__(self, mp_manager: multiprocessing.Manager):
        super(ParallelNotifier, self).__init__()
        self.queue = mp_manager.Queue()
        self.local_queue = mp_manager.Queue()

    def close(self):
        self.queue = None
        self.local_queue = None

    def manage(self, notification):
        # type: (Notification) -> None
        print(notification)
        self.queue.put_nowait(notification)
        self.local_queue.put_nowait(notification)
