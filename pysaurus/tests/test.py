from pysaurus.core.database.api import API
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH
from pysaurus.core import functions

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
    print(sum(1 for _ in api.missing_thumbnails()))
    print(sum(1 for _ in api.database.unreadable.found))


if __name__ == '__main__':
    # main2()
    print(functions.split_words_and_numbers('america228'))
    print(functions.split_words_and_numbers('america228blabla'))
    print(functions.split_words_and_numbers('america228blabla220'))
    print(functions.split_words_and_numbers('544america228blabla220'))
    print(functions.split_words_and_numbers('544america228blabla220sasa'))
    print(functions.split_words_and_numbers('544america228blabla220 sasa 44'))
