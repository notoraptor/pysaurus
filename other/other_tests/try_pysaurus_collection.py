from pysaurus.core.profiling import ConsoleProfiler as Profiler
from pysaurus.core.semantic_text import (
    CharClass,
    get_longest_number_in_string,
    pad_numbers_in_string,
)
from saurus.sql.pysaurus_program import PysaurusProgram
from tests.utils_testing import DB_NAME


def main():
    program = PysaurusProgram()
    with Profiler("collection"):
        collection = program.open_database(DB_NAME)
    with Profiler("count videos"):
        print(DB_NAME, collection.count_videos())
    with Profiler("filenames"):
        filenames = [
            row[0] for row in collection.db.query("SELECT filename FROM video")
        ]
    with Profiler("meta titles"):
        meta_titles = [
            row[0]
            for row in collection.db.query(
                "SELECT meta_title FROM video WHERE meta_title != ''"
            )
        ]
    print("Filenames", len(filenames), "meta titles", len(meta_titles))
    with Profiler("longest"):
        c = max(
            (get_longest_number_in_string(filename) for filename in filenames),
            default=0,
        )
    print("Max:", c)

    text = "My age is 020.444 and⁸⁵³34³³₅ab₅₄₅10₄ my name is Eminem10"
    p = get_longest_number_in_string(text)
    print(p)
    print(CharClass.DIGITS)
    print(CharClass.SUP_DIGITS)
    print(CharClass.SUB_DIGITS)
    print(int("0033"))
    print(text)
    print(pad_numbers_in_string(text, p))


def main2():
    """
    sources
    grouping
    classifier
    group
    search
    sort
    """
    program = PysaurusProgram()
    collection = program.open_database(DB_NAME)
    provider = collection.provider
    provider.set_groups("category", True, allow_singletons=True)
    # provider.set_classifier_path(["0", "01"])
    # provider.set_group(6)
    with Profiler("run provider"):
        indices = provider.get_view_indices()
    print(len(indices))


if __name__ == "__main__":
    main2()
