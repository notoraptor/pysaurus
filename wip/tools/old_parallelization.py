"""Parallelization utilities moved from pysaurus.core.parallelization (unused)."""

import os
from typing import Callable, Iterable

from pysaurus.core.parallelization import parallelize

CPU_COUNT = os.cpu_count() or 1


class Job:
    __slots__ = ("batch", "id", "args")

    def __init__(self, batch: list, job_id: str, args: list | None = None):
        self.batch = batch
        self.id = job_id
        self.args = args or ()


class IterableWithLength(Iterable):
    __slots__ = ("_itr", "_len")

    def __init__(self, iterable: Iterable, length: int):
        self._itr = iterable
        self._len = length

    def __iter__(self):
        return self._itr

    def __len__(self):
        return self._len


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
