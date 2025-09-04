import inspect
import json
import os

from pysaurus.core.duration import Duration
from pysaurus.core.perf_counter import PerfCounter
from pysaurus.database.db_utils import DatabaseLoaded
from saurus.sql.pysaurus_collection import PysaurusCollection
from saurus.sql.pysaurus_program import PysaurusProgram
from wip.examples.command_with_kwargs import parse_command_with_kwargs

Duration


def _format_count_and_unit(size: int, singular: str, plural: str = None) -> str:
    plural = plural or (singular + "s")
    return f"{size} {singular if size < 2 else plural}"


class Example:
    WORKDIR = os.path.dirname(__file__)
    assert os.path.isdir(WORKDIR)

    def __init__(self):
        json_path = os.path.join(self.WORKDIR, "ignored", "example.json")
        with open(json_path) as file:
            example_dict = json.load(file)
        self.database_name = example_dict["database_name"]

        program = PysaurusProgram()
        self.database: PysaurusCollection = program.open_database(self.database_name)

    def folders(self):
        folders = sorted(self.database.get_folders())
        print(_format_count_and_unit(len(folders), "folder"))
        for folder in folders:
            print(f"\t{folder}")

    def prop_types(self):
        prop_types = self.database.get_prop_types()
        print(_format_count_and_unit(len(prop_types), "property type"))
        for prop_type in prop_types:
            name = prop_type["name"]
            property_id = prop_type["property_id"]
            multiple = prop_type["multiple"]
            typ = prop_type["type"]
            enums = prop_type["enumeration"]
            default: list = prop_type["defaultValues"]

            if multiple:
                valuestr = (" in: " + ", ".join(map(repr, enums))) if enums else ""
                typestr = f"[{typ}{valuestr}]"
            else:
                valuestr = (
                    (" in: " + ", ".join(map(repr, enums)))
                    if enums
                    else f" = {repr(default[0])}"
                )
                typestr = f"{typ}{valuestr}"
            print(f"\t({property_id}) {name}: {typestr}")

    def stats(self):
        db_stats = DatabaseLoaded(self.database)
        for key in db_stats.get_slots():
            print(f"\t{key}: {getattr(db_stats, key)}")

    def view(self):
        provider = self.database.provider
        sources = provider.get_sources()
        grouping = provider.get_grouping()
        classifier = provider.get_classifier_path()
        group = provider.get_group()
        search = provider.get_search()
        sorting = provider.get_sort()
        print(f"\tSources: {sources}")
        print(f"\tGrouping: {grouping}")
        print(f"\tClassifier: {classifier}")
        print(f"\tGroup: {group}")
        print(f"\tSearch: {search}")
        print(f"\tSorting: {sorting}")


def main():
    example = Example()
    commands = {}
    for name, value in inspect.getmembers(example, predicate=inspect.ismethod):
        if not name.startswith("_"):
            commands[name] = value

    help_keywords = {"help", "h", "?"}
    exit_keywords = {"exit", "q", "quit", "0"}

    while True:
        try:
            typed = input("[Enter your command, or `help` to get help]: ")
            choice, args = parse_command_with_kwargs(typed)
            if choice in help_keywords:
                print("Available commands:")
                for command in commands.keys():
                    print(f" - {command}")
            elif choice in commands:
                with PerfCounter() as pc:
                    commands[choice](**args)
                print(f"[{choice}] executed in: {Duration(pc.microseconds)}")
            elif choice in exit_keywords:
                print("Exiting...")
                break
            else:
                print("Invalid choice, please try again.")
            print()
        except KeyboardInterrupt:
            print("\nExiting...")
            break


if __name__ == "__main__":
    main()
