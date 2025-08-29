import sys
from abc import ABC, abstractmethod
from typing import Any, Iterable

from pysaurus.core.components import Duration
from pysaurus.core.job_notifications import notify_job_progress, notify_job_start
from pysaurus.core.notifications import ProfilingEnd
from pysaurus.core.perf_counter import PerfCounter


class AbstractNotifier(ABC):
    __slots__ = ()

    @abstractmethod
    def notify(self, notification):
        pass

    def task(
        self, identifier, total: int, kind="item(s)", expectation=None, title=None
    ):
        notify_job_start(self, identifier, total, kind, expectation, title)

    def progress(self, identifier, step: int, size=1, channel=None, title=None):
        notify_job_progress(self, identifier, channel, step, size, title=title)

    def tasks(self, iterable: Iterable, desc: Any, total: int = None, kind="item(s)"):
        if total is None:
            if not hasattr(iterable, "__len__"):
                print("[task_range] converting iterable to list", file=sys.stderr)
                iterable = list(iterable)
            total = len(iterable)
        self.task(desc, total, kind)
        with PerfCounter() as perf_counter:
            for i, element in enumerate(iterable):
                yield element
                if total <= 1_000 or (i + 1) % 200 == 0 or i + 1 == total:
                    self.progress(desc, i + 1, total)
        self.notify(
            ProfilingEnd(desc, Duration(perf_counter.microseconds), inline=True)
        )
