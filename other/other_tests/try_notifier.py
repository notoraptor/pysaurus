"""
discarded unreadable not_found
discarded unreadable found
discarded readable not_found without_thumbnail
discarded readable not_found with_thumbnail
discarded readable found without_thumbnail
discarded readable found with_thumbnail
allowed unreadable not_found
allowed unreadable found
allowed readable not_found without_thumbnail
allowed readable not_found with_thumbnail
allowed readable found without_thumbnail
allowed readable found with_thumbnail
"""

from pysaurus.core.informer import Informer
from pysaurus.core.profiling import Profiler


def main():
    with Informer.default():
        with Profiler("Test"):
            x = 1 + 2


def main2():
    cases = [
        ["discarded", "allowed"],
        ["unreadable", "readable"],
        ["not_found", "found"],
        ["without_thumbnail", "with_thumbnail"],
    ]

    for i in range(2):
        for j in range(2):
            for k in range(2):
                for l in range(2):
                    print(cases[0][i], cases[1][j], cases[2][k], cases[3][l])


if __name__ == "__main__":
    main2()
