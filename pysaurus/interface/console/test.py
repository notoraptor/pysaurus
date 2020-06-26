from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH
from pysaurus.core.database.api import API
from pysaurus.core.database.database import Database
import inspect
import itertools


def main():
    api = API(TEST_LIST_FILE_PATH)
    all_arguments = set(inspect.getargspec(Database.get_videos).args)
    all_arguments.remove('self')
    arguments = sorted(all_arguments)
    print(*arguments)
    count = 0
    for nb_values in range(len(arguments) + 1):
        for true_values in itertools.combinations(arguments, nb_values):
            count += 1
            args = {arg: True for arg in true_values}
            videos = list(api.database.get_videos(**args))
            print('%2d' % count, true_values)
            print('\t', len(videos))


def main2():
    api = API(TEST_LIST_FILE_PATH)
    print(api.database.unreadable)
    print(api.database.unreadable.not_found)
    print(api.database.unreadable.found)
    print(api.database.readable)
    print(api.database.readable.not_found)
    print(api.database.readable.found)
    print(api.database.readable.found.without_thumbnails)
    print(api.database.readable.found.with_thumbnails)


if __name__ == '__main__':
    main2()
