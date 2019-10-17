from pysaurus.core.database.api import API
from pysaurus.core.functions import pgcd
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH
from pysaurus.core.profiling import Profiler
from typing import Tuple


def simplify_fraction(a, b):
    # type: (int, int) -> Tuple[int, int]
    d = pgcd(a, b)
    return a // d, b // d


def compute_fraction(a, b):
    # type: (int, int) -> float
    return a / b


def main():
    api = API(TEST_LIST_FILE_PATH)
    with Profiler('Getting miniatures:'):
        miniatures = api.database.ensure_miniatures()
    print(len(miniatures), 'miniature(s)')
    return
    ratios = {}
    for i, miniature in enumerate(miniatures.values()):
        nb_unique_pixels = len(set(miniature.tuples()))
        nb_pixels = miniature.size
        ratio = simplify_fraction(nb_unique_pixels, nb_pixels)
        if ratio in ratios:
            ratios[ratio] += 1
        else:
            ratios[ratio] = 1
        if (i + 1) % 1000 == 0:
            print(i + 1, '...')
    print(len(ratios), 'ratios,', len(miniatures), 'miniatures')
    iterator_ratio = iter(ratios)
    min_ratio = max_ratio = next(iterator_ratio)
    for ratio in iterator_ratio:
        if compute_fraction(*min_ratio) > compute_fraction(*ratio):
            min_ratio = ratio
        if compute_fraction(*max_ratio) < compute_fraction(*ratio):
            max_ratio = ratio
    print('Min ratio', min_ratio, ratios[min_ratio])
    print('Max ratio', max_ratio, ratios[max_ratio])


if __name__ == '__main__':
    main()
