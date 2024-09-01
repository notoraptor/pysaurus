from abc import ABC, abstractmethod

from pysaurus.core.job_notifications import notify_job_progress, notify_job_start


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
