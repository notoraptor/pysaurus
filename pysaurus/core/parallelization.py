import inspect
import os
from multiprocessing import Pool
from typing import Any, Iterable, List, Optional, Tuple

from pysaurus.core.abstract_notifier import AbstractNotifier


class Job:
    __slots__ = ("batch", "id", "args")

    def __init__(self, batch: list, job_id: str, args: list = None):
        self.batch = batch
        self.id = job_id
        self.args = args or ()


CPU_COUNT = os.cpu_count()
USABLE_CPU_COUNT = max(1, CPU_COUNT - 2)


def run_split_batch(function, tasks, *, job_count=CPU_COUNT, extra_args=None):
    jobs = _dispatch_tasks(tasks, job_count, extra_args)
    return parallelize(function, jobs, cpu_count=job_count)


def _dispatch_tasks(tasks, job_count, extra_args=None):
    # type: (list, int, list) -> List[Job]
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

    def __init__(self, function: callable, notifier: AbstractNotifier):
        self.function = function
        self.notifier = notifier
        self.__name__ = self.function.__name__

    def __call__(self, enumerated_task: Tuple[int, Any]):
        task_id, task = enumerated_task
        ret = self.function(task)
        self.notifier.progress(self.function, 1, 1, task_id)
        return ret


class _StepNotifiedFunction(_NotifiedFunction):
    __slots__ = ("_progress_step",)

    def __init__(self, function: callable, notifier: AbstractNotifier, progress_step=1):
        super().__init__(function, notifier)
        self._progress_step = progress_step
        raise RuntimeError("Should not be called")

    def __call__(self, enumerated_task: Tuple[int, Any]):
        task_id, task = enumerated_task
        ret = self.function(task)
        if (task_id + 1) % self._progress_step == 0:
            self.notifier.progress(self.function, task_id + 1, 0)
        return ret


def _generate_notified_function(
    function, notifier, progress_step=1
) -> _NotifiedFunction:
    return (
        _NotifiedFunction(function, notifier)
        if progress_step < 2
        else _StepNotifiedFunction(function, notifier, progress_step)
    )


def parallelize(
    function,
    tasks: Iterable,
    *,
    cpu_count=CPU_COUNT,
    chunksize=1,
    ordered=True,
    notifier: Optional[AbstractNotifier] = None,
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
        if hasattr(tasks, "__len__"):
            nb_tasks = len(tasks)
        else:
            tasks = list(tasks)
            nb_tasks = len(tasks)
        wrapped_run = _generate_notified_function(run, notifier, progress_step)
        wrapped_tasks = enumerate(tasks)
        notifier.task(wrapped_run, nb_tasks, kind or "task(s)")
    else:
        wrapped_run = run
        wrapped_tasks = tasks

    with Pool(cpu_count) as p:
        mapper = p.imap if ordered else p.imap_unordered
        yield from mapper(wrapped_run, wrapped_tasks, chunksize=chunksize)
