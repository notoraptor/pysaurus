import multiprocessing
import queue
import sys
import threading
import time
from typing import Callable

from pysaurus.core.components import Date
from pysaurus.core.job_notifications import notify_job_progress, notify_job_start
from pysaurus.core.notifications import Notification
from pysaurus.interface.api.api_utils.console_notification_printer import (
    ConsoleNotificationPrinter,
)


class ManagerFactory:
    """
    Static class to provide a multiprocessing manager
    generated once and stored in a class static attribute.
    Used in class below.
    """

    __default__ = None

    @classmethod
    def default(cls):
        if cls.__default__ is None:
            print("INIT MANAGER", file=sys.stderr)
            cls.__default__ = multiprocessing.Manager()
        return cls.__default__


class InformerCallbackFactory:
    __slots__ = ("_callback",)

    def __init__(self):
        self._callback = self._default_callback

    def _default_callback(self, notification: Notification):
        pass

    def set_manager(self, callback: Callable[[Notification], None]):
        self._callback = callback or self._default_callback

    def manage(self, notification: Notification):
        self._callback(notification)


INFORMER_CALLBACK = InformerCallbackFactory()


class Informer:
    __slots__ = ("__queues", "_thread_stop_flag")
    __default__ = None

    def __init__(self, nb_queues: int = 1):
        assert nb_queues > 0
        self.__queues = [ManagerFactory.default().Queue() for _ in range(nb_queues)]
        self._thread_stop_flag = False

    def next(self, queue_id=0):
        try:
            return self.__queues[queue_id].get_nowait()
        except queue.Empty:
            return None

    def next_or_crash(self, queue_id=0):
        return self.__queues[queue_id].get_nowait()

    def consume_main_queue(self):
        yield self.consume(MAIN_QUEUE)

    def consume(self, queue_id):
        while True:
            try:
                yield self.__queues[queue_id].get_nowait()
            except queue.Empty:
                break
        assert not self.__queues[queue_id].qsize()

    def __call__(self, something):
        return self.notify(something)

    def notify(self, something):
        for local_queue in self.__queues:
            local_queue.put_nowait(something)

    def task(self, name, total: int, kind="item(s)", expectation=None, title=None):
        notify_job_start(self, name, total, kind, expectation, title)

    def progress(self, name, step: int, size=1, channel=None, title=None):
        notify_job_progress(self, name, channel, step, size, title=title)

    @classmethod
    def default(cls):
        if cls.__default__ is None:
            print("INIT INFORMER", file=sys.stderr)
            cls.__default__ = cls(2)
        return cls.__default__

    @staticmethod
    def log(filename: str, something):
        with open(filename, "a", encoding="utf-8") as file:
            file.write(f"[{Date.now()}] {something}\n")

    def _monitor(self):

        # We are in a thread, with notifications handled sequentially,
        # thus no need to be process-safe.
        print("Monitoring notifications ...")
        notification_printer = ConsoleNotificationPrinter()
        while True:
            if self._thread_stop_flag:
                break
            try:
                notification = self.next_or_crash()
                notification_printer.print(notification)
                INFORMER_CALLBACK.manage(notification)
            except queue.Empty:
                time.sleep(1 / 100)
        print("Monitoring stopped, clearing queue.")
        while True:
            try:
                notification = self.next_or_crash()
                notification_printer.print(notification)
                INFORMER_CALLBACK.manage(notification)
            except queue.Empty:
                break
        print("End monitoring.")

    def __enter__(self):
        th = threading.Thread(target=self._monitor)
        th.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._thread_stop_flag = True


MAIN_QUEUE = 0
PROVIDER_QUEUE = 1
