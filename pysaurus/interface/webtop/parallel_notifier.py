import multiprocessing

from pysaurus.core.notifications import Notification
from pysaurus.core.notifier import Notifier


class ParallelNotifier(Notifier):
    __slots__ = ("queue",)

    def __init__(self, shared_queue):
        # type: (multiprocessing.Queue) -> None
        super(ParallelNotifier, self).__init__()
        self.queue = shared_queue

    def manage(self, notification):
        # type: (Notification) -> None
        print(notification)
        self.queue.put_nowait(notification)
