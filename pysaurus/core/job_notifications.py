import sys
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


class ConsoleJobProgress:
    __slots__ = "job_to_do", "channels", "shift"

    def __init__(self, job_to_do: JobToDo):
        self.job_to_do = job_to_do
        self.channels = {}
        self.shift = 0
        print(job_to_do)
        self._progress(0)

    @property
    def done(self):
        return self.job_to_do.total == sum(self.channels.values(), start=0)

    def update(self, job_step: JobStep):
        assert self.job_to_do.name == job_step.name
        self.channels[job_step.channel] = job_step.step
        self._progress(sum(self.channels.values()))

    def _progress(self, step: int):
        """Manual console progress bar.

        NB: We cannot use tqdm here, because:
        - tqdm object cannot be pickled across processes.
        - I don't know how to recreate a tqdm attached to previous bar
          (new tqdm object will automatically write on next line).
        """
        total = self.job_to_do.total
        length_bar = 30
        length_done = int(length_bar * step / total) if total else length_bar
        output = (
            f"|{'█' * length_done}{' ' * (length_bar - length_done)}| "
            f"{step}/{total} {self.job_to_do.title}"
        )
        sys.stdout.write(("\r" * self.shift) + output)
        self.shift = len(output)
        if step == total:
            sys.stdout.write("\r\n")


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


def notify_job_start(notifier, identiifier, total, kind, expectation=None, title=None):
    name = _get_job_name(identiifier)
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
