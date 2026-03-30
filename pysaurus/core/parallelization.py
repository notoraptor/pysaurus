import inspect
import os
from multiprocessing import Pool
from typing import Any, Callable, Iterable, Sized

from pysaurus.core.job_notifications import AbstractNotifier


CPU_COUNT = os.cpu_count() or 1
USABLE_CPU_COUNT = max(1, CPU_COUNT - 2)


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
