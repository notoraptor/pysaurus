from collections.abc import Callable

from pysaurus.core.components import Duration
from pysaurus.core.perf_counter import PerfCounter

inf = float("inf")
big = 10
x = 12
width = 44


def check_float(limit):
    return x and x + width > limit


def check_optional(limit):
    return limit is not None and x and x + width > limit


def benchmark(batch_size: int, function: Callable, *args, **kwargs):
    with PerfCounter() as pc:
        for _ in range(batch_size):
            function(*args, **kwargs)
    print(function.__name__, Duration(pc.microseconds))


def main():
    batch_size = 10_000_000
    benchmark(batch_size, check_float, inf)
    benchmark(batch_size, check_optional, big)


if __name__ == "__main__":
    main()
