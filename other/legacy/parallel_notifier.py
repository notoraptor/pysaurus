"""
Notifier to use if to be shared across multiple processes.

Each notification in stored in 2 queues.
Queues must then be consumed in any process or thread to manage notifications.

Q: Why 2 queues instead of just 1.
A:
    Originally, each notification should be used in 2 ways, leading to use 2 queues.
    - Send notification to interface for live refreshing.
    - Send notification to database provider for view refreshing.
      View is not live-refreshed, it is instead refreshed only when a certain function
      is called. So, the 2nd queue allows to accumulate notifications between 2
      calls to refresh function. On each refresh, 2nd queue is entirely consumed,
      to get all latest accumulated notifications.
"""

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

    def manage(self, notification: Notification) -> None:
        # print(notification)
        self.queue.put_nowait(notification)
        self.local_queue.put_nowait(notification)
