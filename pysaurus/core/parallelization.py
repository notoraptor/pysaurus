import inspect
import os
from multiprocessing import Pool
from typing import Any, Callable, Iterable, Sized

from pysaurus.core.job_notifications import AbstractNotifier


class Job:
    __slots__ = ("batch", "id", "args")

    def __init__(self, batch: list, job_id: str, args: list | None = None):
        self.batch = batch
        self.id = job_id
        self.args = args or ()


CPU_COUNT = os.cpu_count() or 1
USABLE_CPU_COUNT = max(1, CPU_COUNT - 2)


def run_split_batch(
    function: Callable,
    tasks: list,
    *,
    job_count: int = CPU_COUNT,
    extra_args: list | None = None,
):
    jobs = _dispatch_tasks(tasks, job_count, extra_args)
    return parallelize(function, jobs, cpu_count=job_count)


def _dispatch_tasks(
    tasks: list, job_count: int, extra_args: list | None = None
) -> list[Job]:
    """Split <tasks> into <job_count> jobs and associate each one
    with a unique job ID starting from <next_job_id>, so that
    each job could assign a unique ID to each of his task by
    incrementing his job ID when managing his tasks.
    :param tasks: a list of tasks to split.
    :param job_count: number of jobs.
    :param extra_args: (optional) list
    :return: a list of Job instances
    """
    if extra_args is None:
        extra_args = []
    task_count = len(tasks)
    if job_count > task_count:
        job_lengths = [1] * task_count
    else:
        q = task_count // job_count
        r = task_count % job_count
        job_lengths = ([q + 1] * r) + ([q] * (job_count - r))
    assert sum(job_lengths) == task_count
    cursor = 0
    jobs = []
    job_id = 0
    job_count = len(job_lengths)
    for job_len in job_lengths:
        job_id += 1
        jobs.append(
            Job(
                tasks[cursor : (cursor + job_len)], f"{job_id}on{job_count}", extra_args
            )
        )
        cursor += job_len
    # NB: next_job_id is now next_job_id + len(tasks).
    return jobs


class _Unpacker:
    __slots__ = ("function", "__name__")

    def __init__(self, function):
        self.function = function
        self.__name__ = function.__name__

    def __call__(self, task):
        return self.function(*task)


class _NotifiedFunction:
    __slots__ = ("function", "notifier", "__name__")

    def __init__(self, function: Callable, notifier: AbstractNotifier):
        self.function = function
        self.notifier = notifier
        self.__name__ = getattr(self.function, "__name__", "")

    def __call__(self, enumerated_task: tuple[int, Any]):
        task_id, task = enumerated_task
        ret = self.function(task)
        self.notifier.progress(self.function, 1, 1, task_id)
        return ret


class IterableWithLength(Iterable):
    __slots__ = ("_itr", "_len")

    def __init__(self, iterable: Iterable, length: int):
        self._itr = iterable
        self._len = length

    def __iter__(self):
        return self._itr

    def __len__(self):
        return self._len


def parallelize(
    function,
    tasks: Iterable,
    *,
    cpu_count=CPU_COUNT,
    chunksize=1,
    ordered=True,
    notifier: AbstractNotifier | None = None,
    kind="",
    progress_step=1,
):
    fn_sgn = inspect.signature(function)
    nb_params = len(fn_sgn.parameters)
    # Function must wait for at least 1 parameter
    assert nb_params
    if nb_params > 1:
        # Assume tasks is an iterable of expandable elements
        run = _Unpacker(function)
    else:
        # Assume tasks is an iterable of non-expandable elements
        run = function

    if notifier:
        if isinstance(tasks, Sized):
            nb_tasks = len(tasks)
        else:
            tasks = list(tasks)
            nb_tasks = len(tasks)
        if progress_step > 1:
            assert ordered
            notifier.task(run, nb_tasks, kind or "task(s)")
            with Pool(cpu_count) as p:
                for i, result in enumerate(p.imap(run, tasks, chunksize=chunksize)):
                    yield result
                    if (i + 1) % progress_step == 0 or i + 1 == nb_tasks:
                        notifier.progress(run, i + 1, nb_tasks)
            return
        wrapped_run = _NotifiedFunction(run, notifier)
        wrapped_tasks = enumerate(tasks)
        notifier.task(wrapped_run, nb_tasks, kind or "task(s)")
    else:
        wrapped_run = run
        wrapped_tasks = tasks

    with Pool(cpu_count) as p:
        mapper = p.imap if ordered else p.imap_unordered
        yield from mapper(wrapped_run, wrapped_tasks, chunksize=chunksize)
