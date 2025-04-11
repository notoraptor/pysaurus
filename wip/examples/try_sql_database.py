import json
import os
import pprint

from saurus.sql.pysaurus_program import PysaurusProgram


class Example:
    WORKDIR = os.path.dirname(__file__)
    assert os.path.isdir(WORKDIR)

    def __init__(self):
        json_path = os.path.join(self.WORKDIR, "ignored", "example.json")
        with open(json_path) as file:
            example_dict = json.load(file)
        self.database_name = example_dict["database_name"]

        program = PysaurusProgram()
        self.database = program.open_database(self.database_name)

    def check_folders(self):
        folders = sorted(self.database.get_folders())
        print(len(folders))
        for folder in folders:
            print(folder)

    def check_prop_types(self):
        prop_types = self.database.get_prop_types()
        print(len(prop_types))
        for prop_type in prop_types:
            pprint.pprint(prop_type)


def main():
    example = Example()
    example.check_prop_types()


if __name__ == "__main__":
    main()
