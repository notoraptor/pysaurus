from typing import Optional

from pysaurus.core.functions import camel_case_to_snake_case
from pysaurus.core.notifications import Notification


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
        channel: Optional[str],
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
            assert total
            assert kind
            expectation = f"{total} {kind}"
        title = f"{description} ({expectation})"
    return title


def notify_job_start(notifier, function, total, kind, expectation=None, title=None):
    name = _get_job_name(function)
    job_title = _compute_job_title(title, name, expectation, total, kind)
    notifier.notify(JobToDo(name, total, job_title))
    if total:
        notifier.notify(JobStep(name, None, 0, total, title=job_title))


def notify_job_progress(
    notifier,
    function,
    channel: Optional[str],
    channel_step: int,
    channel_size: int,
    *,
    title: str = None,
):
    notifier.notify(
        JobStep(
            _get_job_name(function), channel, channel_step, channel_size, title=title
        )
    )
