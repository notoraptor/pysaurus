import concurrent.futures
from typing import List


class Job:
    __slots__ = ("batch", "id", "args")

    def __init__(self, batch: list, job_id: str, args: list = None):
        self.batch = batch
        self.id = job_id
        self.args = args or ()


def run_split_batch(function, tasks, job_count, extra_args=None):
    jobs = dispatch_tasks(tasks, job_count, extra_args)
    return parallelize(function, jobs, job_count)


def dispatch_tasks(tasks, job_count, extra_args=None):
    # type: (list, int, list) -> List[Job]
    """Split <tasks> into <job_count> jobs and associate each one
    with an unique job ID starting from <next_job_id>, so that
    each job could assign an unique ID to each of his task by
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
        job_lengths = [task_count // job_count] * job_count
        for i in range(task_count % job_count):
            job_lengths[i] += 1
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


def parallelize(function, jobs, cpu_count):
    with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
        results = list(executor.map(function, jobs))
    return results
