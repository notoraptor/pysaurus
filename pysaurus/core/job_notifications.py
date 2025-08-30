import sys
from abc import ABC, abstractmethod
from typing import Any, Iterable

from pysaurus.core.components import Duration
from pysaurus.core.functions import camel_case_to_snake_case
from pysaurus.core.notifications import Notification, ProfilingEnd, ProfilingStart
from pysaurus.core.perf_counter import PerfCounter


class JobToDo(Notification):
    __slots__ = "name", "total", "title"

    def __init__(self, name: str, total: int, title: str = None):
        self.name = name
        self.total = total
        self.title = title


class JobStep(Notification):
    __slots__ = "name", "channel", "step", "total", "title"
    __slot_sorter__ = list

    def __init__(
        self,
        name: str,
        channel: str | None,
        step: int,
        total: int,
        *,
        title: str = None,
    ):
        self.name = name
        self.channel = channel
        self.step = step
        self.total = total
        self.title = title


def _get_job_name(fn_or_name):
    return (
        camel_case_to_snake_case(
            fn_or_name if isinstance(fn_or_name, str) else fn_or_name.__name__
        )
        .replace("_", " ")
        .strip()
    )


def _compute_job_title(title, description, expectation, total, kind):
    if title is None:
        assert description
        if expectation is None:
            # assert total
            # assert kind
            expectation = f"{total} {kind}"
        title = f"{description} ({expectation})"
    return title


class JobProgressDisplay:
    __slots__ = "job_to_do", "channels"

    def __init__(self, job_to_do: JobToDo):
        self.job_to_do = job_to_do
        self.channels = {}
        print(job_to_do)
        self._display(0)

    @property
    def done(self) -> bool:
        return self.job_to_do.total == self.current

    @property
    def current(self) -> int:
        return sum(self.channels.values(), start=0)

    @property
    def total(self) -> int:
        return self.job_to_do.total

    @property
    def title(self) -> str:
        return self.job_to_do.title

    def update(self, job_step: JobStep):
        assert self.job_to_do.name == job_step.name
        self.channels[job_step.channel] = job_step.step
        self._display(sum(self.channels.values()))

    def _display(self, step: int):
        pass


class NotificationCollector:
    __slots__ = ("progressions", "profiles", "nb_notifications", "views")

    def __init__(self):
        self.profiles: dict[str, int] = {}
        self.progressions: dict[str, JobProgressDisplay] = {}
        self.nb_notifications: int = 0
        self.views = []

    def collect(self, notification):
        self.nb_notifications += 1

        if isinstance(notification, ProfilingStart):
            assert notification.name not in self.profiles
            self.profiles[notification.name] = self.nb_notifications
        elif isinstance(notification, ProfilingEnd):
            if notification.inline:
                assert notification.name not in self.profiles, notification
            else:
                assert notification.name in self.profiles
                index_start = self.profiles.pop(notification.name)
                # If ProfilingEnd just follows ProfilingStart,
                # we want to inline notification.
                notification = notification.with_inline(
                    self.nb_notifications == index_start + 1
                )
            self.display_notification(notification)
        elif isinstance(notification, JobToDo):
            assert notification.name not in self.progressions
            self.progressions[notification.name] = self.new_progress(notification)
        elif isinstance(notification, JobStep):
            assert notification.name in self.progressions
            progress = self.progressions[notification.name]
            progress.update(notification)
            if progress.done:
                del self.progressions[notification.name]
        else:
            self.display_notification(notification)

    def display_notification(self, notification: Notification):
        self.views.append(notification)
        self._display_notification(notification)

    def new_progress(self, job_to_do: JobToDo) -> JobProgressDisplay:
        progress = self._new_progress(job_to_do)
        self.views.append(progress)
        return progress

    def _display_notification(self, notification: Notification):
        pass

    def _new_progress(self, job_to_do: JobToDo) -> JobProgressDisplay:
        return JobProgressDisplay(job_to_do)


class AbstractNotifier(ABC):
    __slots__ = ()

    @abstractmethod
    def notify(self, notification):
        pass

    def task(
        self, identifier, total: int, kind="item(s)", expectation=None, title=None
    ):
        """Job start"""
        name = _get_job_name(identifier)
        job_title = _compute_job_title(title, name, expectation, total, kind)
        self.notify(JobToDo(name, total, job_title))
        if total:
            self.notify(JobStep(name, None, 0, total, title=job_title))

    def progress(self, identifier, step: int, size=1, channel=None, title=None):
        """Job progress"""
        self.notify(
            JobStep(_get_job_name(identifier), channel, step, size, title=title)
        )

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
