import functools

from pysaurus.core.components import Duration
from pysaurus.core.informer import Informer
from pysaurus.core.notifications import ProfilingEnd, ProfilingStart
from pysaurus.core.notifying import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.perf_counter import PerfCounter


class Profiler(PerfCounter):
    __slots__ = "_title", "_notifier", "_inline"

    def __init__(self, title, notifier=None, inline=False):
        self._title = title
        self._notifier = notifier or Informer.default()
        self._inline = inline
        super().__init__()

    def __enter__(self):
        if not self._inline:
            self._notifier.notify(ProfilingStart(self._title))
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        self._notifier.notify(
            ProfilingEnd(self._title, Duration(self.microseconds), inline=self._inline)
        )

    @staticmethod
    def profile(title=None):
        """Profile a function."""

        def decorator_profile(fn):
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                with Profiler(title or fn.__name__):
                    return fn(*args, **kwargs)

            return wrapper

        return decorator_profile

    @staticmethod
    def profile_method(title=None):
        """Profile a method from an object providing a `notifier` attribute."""

        def decorator_profile(fn):
            @functools.wraps(fn)
            def wrapper(self, *args, **kwargs):
                with Profiler(title or fn.__name__, notifier=self.notifier):
                    return fn(self, *args, **kwargs)

            return wrapper

        return decorator_profile


class ConsoleProfiler(Profiler):
    __slots__ = ()

    def __init__(self, title, stderr=False):
        super().__init__(title, notifier=((stderr and DEFAULT_NOTIFIER) or Notifier()))


class InlineProfiler(Profiler):
    __slots__ = ()

    def __init__(self, title, notifier=DEFAULT_NOTIFIER):
        super().__init__(title, notifier)
