import multiprocessing
import sys
import threading
from typing import Callable

from pysaurus.core.components import Date
from pysaurus.core.job_notifications import AbstractNotifier
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


class Informer(AbstractNotifier):
    __slots__ = ("__queue",)
    __default__ = None

    def __init__(self):
        self.__queue = ManagerFactory.default().Queue()

    def __call__(self, something):
        return self.notify(something)

    def notify(self, something):
        self.__queue.put_nowait(something)

    @classmethod
    def default(cls):
        if cls.__default__ is None:
            print("INIT INFORMER", file=sys.stderr)
            cls.__default__ = cls()
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
            notification = self.__queue.get()
            if notification is None:
                break
            notification_printer.collect(notification)
            INFORMER_CALLBACK.manage(notification)
        print("End monitoring.")

    def __enter__(self):
        th = threading.Thread(target=self._monitor)
        th.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__queue.put(None)
