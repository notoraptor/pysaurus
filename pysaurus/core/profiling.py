import functools
import time
from datetime import timedelta

from pysaurus.core.components import Duration
from pysaurus.core.informer import Informer
from pysaurus.core.notifications import Notification


class ProfilingStart(Notification):
    __slots__ = ("name",)

    def __init__(self, title):
        # type: (str) -> None
        self.name = title

    def __str__(self):
        return f"ProfilingStart({self.name})"

    __repr__ = __str__


class ProfilingEnd(Notification):
    __slots__ = "name", "time"

    def __init__(self, name, duration):
        self.name = name
        self.time = str(duration)

    def __str__(self):
        return f"ProfilingEnded({self.name}, {self.time})"


class _Profile(Duration):
    __slots__ = ()

    def __init__(self, difference: timedelta):
        super().__init__(
            (difference.seconds + difference.days * 24 * 3600) * 1_000_000
            + difference.microseconds
        )


class _InlineProfile(Notification):
    __slots__ = "title", "time"

    def __init__(self, title, duration):
        self.title = title
        self.time = duration

    def __str__(self):
        return f"Profiled({self.title}, {self.time})"


class Profiler:
    __slots__ = "__title", "__time_start", "__time_end", "__notifier", "__inline"

    def __init__(self, title, notifier=None, inline=False):
        self.__title = title
        self.__notifier = notifier or Informer.default()
        self.__time_start = None
        self.__time_end = None
        self.__inline = inline

    def __enter__(self):
        if not self.__inline:
            self.__notifier.notify(ProfilingStart(self.__title))
        self.__time_start = time.perf_counter_ns()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__time_end = time.perf_counter_ns()
        profiling = _Profile(
            timedelta(microseconds=(self.__time_end - self.__time_start) / 1000)
        )
        if self.__inline:
            self.__notifier.notify(_InlineProfile(self.__title, profiling))
        else:
            self.__notifier.notify(ProfilingEnd(self.__title, profiling))

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


class InlineProfiler(Profiler):
    __slots__ = ()

    def __init__(self, title, notifier=None):
        super().__init__(title, notifier, True)
