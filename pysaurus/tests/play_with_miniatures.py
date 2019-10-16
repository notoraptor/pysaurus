from pysaurus.core.database.api import API
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH


def _pgcd(a, b):
    return a if not b else _pgcd(b, a % b)


def pgcd(a, b):
    if a < b:
        a, b = b, a
    return _pgcd(a, b)


def frac(a, b):
    d = pgcd(a, b)
    return a // d, b // d


def _double(a, b):
    return a / b


def main():
    api = API(TEST_LIST_FILE_PATH)
    miniatures = api.database.ensure_miniatures()
    print(len(miniatures), 'miniature(s)')
    ratios = {}
    for i, miniature in enumerate(miniatures.values()):
        nb_unique_pixels = len(set(miniature.tuples()))
        nb_pixels = miniature.size
        ratio = frac(nb_unique_pixels, nb_pixels)
        if ratio in ratios:
            ratios[ratio] += 1
        else:
            ratios[ratio] = 1
        if (i + 1) % 1000 == 0:
            print(i + 1, '...')
    print(len(ratios), 'ratios', len(miniatures), 'miniatures')
    iterator_ratio = iter(ratios)
    min_ratio = max_ratio = next(iterator_ratio)
    for ratio in iterator_ratio:
        if _double(*min_ratio) > _double(*ratio):
            min_ratio = ratio
        if _double(*max_ratio) < _double(*ratio):
            max_ratio = ratio
    print('Min ratio', min_ratio, ratios[min_ratio])
    print('Max ratio', max_ratio, ratios[max_ratio])

if __name__ == '__main__':
    main()
