import time


class PerfCounter:
    __slots__ = ("_ns_start", "_ns_end")

    def __init__(self):
        self._ns_start = self._ns_end = 0

    def __enter__(self):
        self._ns_start = time.perf_counter_ns()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ns_end = time.perf_counter_ns()

    @property
    def nanoseconds(self) -> float:
        return self._ns_end - self._ns_start

    @property
    def microseconds(self) -> float:
        return (self._ns_end - self._ns_start) / 1000
