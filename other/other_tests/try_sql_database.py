from pysaurus.core.profiling import ConsoleProfiler
from tests.test_pysaurus_collection import get_memory_sql_collection
from tests.utils_testing import DB_NAME


def main():
    print("Database:", DB_NAME)
    collection = get_memory_sql_collection(DB_NAME)

    with ConsoleProfiler("get all video terms"):
        collection.get_all_video_terms()

    prop_name = "keywords"
    assert not collection.get_prop_types(name=prop_name)
    collection.create_prop_type(prop_name, str, "", True)
    with ConsoleProfiler("fill property with keywords"):
        collection.fill_property_with_terms(prop_name)
    props = collection.get_all_prop_values(prop_name)
    video_id = next(iter(props))
    print(props[video_id])


if __name__ == "__main__":
    main()
