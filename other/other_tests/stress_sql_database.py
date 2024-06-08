import sqlite3

from pysaurus.core.profiling import ConsoleProfiler as Profiler
from saurus.sql.pysaurus_program import PysaurusProgram
from tests.utils_testing import DB_NAME


def get_collection():
    with Profiler("get_collection"):
        name = DB_NAME
        print(f"Opening database: {name} ...")
        program = PysaurusProgram()
        collection = program.open_database(name)
        memory_connection = sqlite3.connect(":memory:")
        collection.db.connection.backup(memory_connection)
        collection.db.connection = memory_connection
        return collection


def main():
    collection = get_collection()
    with Profiler("count_videos"):
        print(collection.count_videos("readable", discarded=False))


if __name__ == "__main__":
    main()
