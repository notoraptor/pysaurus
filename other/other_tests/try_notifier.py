from pysaurus.core.informer import Informer
from pysaurus.core.profiling import Profiler


def main():
    with Informer.default():
        with Profiler("Test"):
            x = 1 + 2


if __name__ == "__main__":
    main()
