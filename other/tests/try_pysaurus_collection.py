from other.tests.utils_testing import DB_NAME
from saurus.sql.pysaurus_program import PysaurusProgram


def main():
    program = PysaurusProgram()
    collection = program.open_database(DB_NAME)
    print(collection.get_prop_values(2, "note"))


if __name__ == "__main__":
    main()
