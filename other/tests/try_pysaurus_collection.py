import pprint

from other.tests.utils_testing import DB_NAME
from pysaurus.core.notifying import Notifier
from pysaurus.core.profiling import Profiler
from saurus.sql.pysaurus_program import PysaurusProgram


def main():
    program = PysaurusProgram()
    collection = program.open_database(DB_NAME)
    print(collection.get_prop_values(2, "note"))
    with Profiler("get videos", Notifier()):
        res = collection.get_videos(with_moves=True)
        print(len(res))
        pprint.pprint(res[0])


if __name__ == "__main__":
    main()
