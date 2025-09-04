import multiprocessing
import sys
import threading
from typing import Callable

from pysaurus.core.datestring import Date
from pysaurus.core.functions import do_nothing
from pysaurus.core.job_notifications import AbstractNotifier
from pysaurus.core.notifications import Notification
from pysaurus.interface.api.api_utils.console_notification_printer import (
    ConsoleNotificationPrinter,
)


class _InformationNotifier(AbstractNotifier):
    __slots__ = ("_queue",)

    def __init__(self, shared_queue):
        self._queue = shared_queue

    def notify(self, notification):
        self._queue.put_nowait(notification)


class Information:
    __slots__ = ("_manager", "_queue", "_thread", "_callback", "_initialized")
    __default__ = None

    def __new__(cls, *args, **kwargs):
        if cls.__default__ is None:
            print("NEW INFORMATION", file=sys.stderr)
            cls.__default__ = super().__new__(cls, *args, **kwargs)
            cls.__default__._initialized = False
        return cls.__default__

    def __init__(self):
        if not getattr(self, "_initialized", False):
            print("INIT INFORMATION", file=sys.stderr)
            self._manager = multiprocessing.Manager()
            self._queue = self._manager.Queue()
            self._thread = None
            self._callback = do_nothing
            self._initialized = True

    def _set_callback(self, callback: Callable[[Notification], None]):
        self._callback = callback or do_nothing

    def __enter__(self):
        if self._thread is None:
            th = threading.Thread(target=self._monitor)
            th.start()
            self._thread = th
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self._thread
        self._queue.put(None)
        self._thread.join()
        self._thread = None

    def _monitor(self):
        # We are in a thread, with notifications handled sequentially,
        # thus no need to be process-safe.
        print("Monitoring notifications ...")
        notification_printer = ConsoleNotificationPrinter()
        while True:
            notification = self._queue.get()
            if notification is None:
                break
            notification_printer.collect(notification)
            self._callback(notification)
        print("End monitoring.")

    @classmethod
    def _get(cls):
        if cls.__default__ is None:
            cls.__default__ = cls()
        return cls.__default__

    @classmethod
    def handle_with(cls, callback: Callable[[Notification], None]):
        cls._get()._set_callback(callback)

    @classmethod
    def notifier(cls) -> _InformationNotifier:
        return _InformationNotifier(cls._get()._queue)

    @staticmethod
    def log(filename: str, something):
        with open(filename, "a", encoding="utf-8") as file:
            file.write(f"[{Date.now()}] {something}\n")
