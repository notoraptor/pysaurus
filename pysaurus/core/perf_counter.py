import time


class PerfCounter:
    __slots__ = ("nanoseconds_start", "nanoseconds_end")

    def __init__(self):
        self.nanoseconds_start = self.nanoseconds_end = 0

    def __enter__(self):
        self.nanoseconds_start = time.perf_counter_ns()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.nanoseconds_end = time.perf_counter_ns()

    @property
    def nanoseconds(self) -> int:
        return self.nanoseconds_end - self.nanoseconds_start
