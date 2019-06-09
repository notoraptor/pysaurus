import multiprocessing

from pysaurus.core.notification import Notification, Notifier


class CoreNotificationCollector(Notifier):
    __slots__ = ('queue',)

    def __init__(self, shared_queue):
        # type: (multiprocessing.Queue) -> None
        super(CoreNotificationCollector, self).__init__()
        self.queue = shared_queue
        self.set_default_manager(self.collect)

    def collect(self, notification):
        # type: (Notification) -> None
        self.queue.put_nowait(notification)
