import multiprocessing

from pysaurus.core.job_notifications import (
    AbstractNotifier,
    JobStep,
    JobToDo,
    NotificationCollector,
)
from pysaurus.core.parallelization import parallelize


class _QueueNotifier(AbstractNotifier):
    """Notifier backed by a multiprocessing Manager Queue proxy
    (picklable, like _InformationNotifier in the real code).
    The Manager must be kept alive externally."""

    __slots__ = ("_queue",)

    def __init__(self, queue):
        self._queue = queue

    def notify(self, notification):
        self._queue.put_nowait(notification)

    def drain(self):
        items = []
        while not self._queue.empty():
            items.append(self._queue.get_nowait())
        return items


def _make_notifier():
    """Create a Manager + notifier pair. Caller must keep manager alive."""
    manager = multiprocessing.Manager()
    return manager, _QueueNotifier(manager.Queue())


def _square(x):
    return x * x


def _add(a, b):
    return a + b


class TestParallelizeWithoutNotifier:
    def test_single_param_function(self):
        results = list(parallelize(_square, [1, 2, 3, 4, 5]))
        assert results == [1, 4, 9, 16, 25]

    def test_multi_param_function(self):
        results = list(parallelize(_add, [(1, 2), (3, 4), (5, 6)]))
        assert results == [3, 7, 11]

    def test_empty_tasks(self):
        results = list(parallelize(_square, []))
        assert results == []


class TestParallelizeWithNotifier:
    def test_progress_step_1_sends_per_task_notifications(self):
        manager, notifier = _make_notifier()
        results = list(
            parallelize(_square, [10, 20, 30], notifier=notifier, kind="items")
        )
        assert results == [100, 400, 900]

        notifications = notifier.drain()
        job_to_dos = [n for n in notifications if isinstance(n, JobToDo)]
        assert len(job_to_dos) == 1
        assert job_to_dos[0].total == 3

        steps = [n for n in notifications if isinstance(n, JobStep)]
        # Initial step (step=0) + one per task
        assert len(steps) == 4
        assert steps[0].step == 0
        assert steps[0].channel is None
        # Each task uses its own channel
        channels = {s.channel for s in steps[1:]}
        assert len(channels) == 3

    def test_progress_step_gt_1_sends_stepped_notifications(self):
        manager, notifier = _make_notifier()
        tasks = list(range(109))
        results = list(
            parallelize(
                _square, tasks, notifier=notifier, kind="items", progress_step=100
            )
        )
        assert results == [x * x for x in range(109)]

        notifications = notifier.drain()
        steps = [n for n in notifications if isinstance(n, JobStep)]
        # Initial step (step=0) + step at 100 + step at 109
        assert len(steps) == 3
        assert steps[0].step == 0
        assert steps[1].step == 100
        assert steps[2].step == 109

    def test_progress_step_exact_multiple(self):
        manager, notifier = _make_notifier()
        tasks = list(range(200))
        results = list(
            parallelize(
                _square, tasks, notifier=notifier, kind="items", progress_step=100
            )
        )
        assert len(results) == 200

        notifications = notifier.drain()
        steps = [n for n in notifications if isinstance(n, JobStep)]
        # Initial step (step=0) + step at 100 + step at 200
        assert len(steps) == 3
        assert steps[1].step == 100
        assert steps[2].step == 200

    def test_progress_step_larger_than_total(self):
        manager, notifier = _make_notifier()
        results = list(
            parallelize(
                _square, [1, 2, 3], notifier=notifier, kind="items", progress_step=100
            )
        )
        assert results == [1, 4, 9]

        notifications = notifier.drain()
        steps = [n for n in notifications if isinstance(n, JobStep)]
        # Initial step (step=0) + final step at 3
        assert len(steps) == 2
        assert steps[1].step == 3

    def test_empty_tasks_with_notifier(self):
        manager, notifier = _make_notifier()
        results = list(
            parallelize(_square, [], notifier=notifier, kind="items", progress_step=10)
        )
        assert results == []
        # task() returns early when total=0, so no notifications
        assert len(notifier.drain()) == 0


class TestParallelizeWithCollector:
    """Verify that notifications from parallelize are compatible with
    NotificationCollector (i.e. the assert in collect() does not fire)."""

    def _run_and_collect(self, tasks, progress_step=1):
        manager, notifier = _make_notifier()
        results = list(
            parallelize(
                _square,
                tasks,
                notifier=notifier,
                kind="items",
                progress_step=progress_step,
            )
        )
        collector = NotificationCollector()
        for n in notifier.drain():
            collector.collect(n)
        return results, collector

    def test_step_1_collector_done(self):
        results, collector = self._run_and_collect(list(range(10)))
        assert results == [x * x for x in range(10)]
        assert len(collector.progressions) == 0

    def test_stepped_collector_done(self):
        results, collector = self._run_and_collect(list(range(109)), progress_step=100)
        assert results == [x * x for x in range(109)]
        assert len(collector.progressions) == 0

    def test_stepped_exact_multiple_collector_done(self):
        results, collector = self._run_and_collect(list(range(200)), progress_step=100)
        assert len(results) == 200
        assert len(collector.progressions) == 0

    def test_stepped_small_collector_done(self):
        results, collector = self._run_and_collect([1, 2, 3], progress_step=100)
        assert results == [1, 4, 9]
        assert len(collector.progressions) == 0

    def test_stepped_notifications_arrive_in_order(self):
        """Verify that with progress_step > 1, step values are monotonically
        increasing — guaranteeing that each reported step truly reflects
        the number of completed tasks."""
        manager, notifier = _make_notifier()
        list(
            parallelize(
                _square,
                list(range(350)),
                notifier=notifier,
                kind="items",
                progress_step=100,
            )
        )
        notifications = notifier.drain()
        steps = [n for n in notifications if isinstance(n, JobStep)]
        step_values = [s.step for s in steps]
        # Must be strictly increasing
        for i in range(1, len(step_values)):
            assert step_values[i] > step_values[i - 1]
