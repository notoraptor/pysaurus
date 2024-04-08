"""
NB: One can put tests in a class, with class name starting with "Test
and testing method names starting with "test_". but this class must
not have a __init__ method:
https://docs.pytest.org/en/7.1.x/explanation/goodpractices.html#test-discovery
"""
import os
import sqlite3

from saurus.sql.pysaurus_program import PysaurusProgram


def get_memory_sql_collection(name: str, *, home_dir=None):
    program = PysaurusProgram(home_dir=home_dir)
    collection = program.open_database(name)
    memory_connection = sqlite3.connect(":memory:")
    collection.db.connection.backup(memory_connection)
    collection.db.connection = memory_connection
    return collection


def get_collection():
    home_dir = os.path.join(os.path.dirname(__file__), "home_dir_test")
    name = "example_db_in_pysaurus"
    return get_memory_sql_collection(name=name, home_dir=home_dir)


def get_provider():
    collection = get_collection()
    # collection.db.debug = True
    return collection.provider


def test_provider():
    with get_provider() as provider:
        indices = provider.get_view_indices()
        assert len(indices) == 90


def test_provider_sources():
    with get_provider() as provider:
        assert len(provider.get_view_indices()) == 90

        provider.set_sources([["not_found"]])
        assert len(provider.get_view_indices()) == 3

        provider.set_sources([["found"]])
        assert len(provider.get_view_indices()) == 90

        provider.set_sources([["unreadable"]])
        assert len(provider.get_view_indices()) == 3

        provider.set_sources([["readable", "without_thumbnails"]])
        assert len(provider.get_view_indices()) == 0

        provider.set_sources([["readable", "with_thumbnails"]])
        assert len(provider.get_view_indices()) == 90

        provider.set_sources([["unreadable"], ["readable"]])
        assert len(provider.get_view_indices()) == 93


def test_provider_grouping_by_attribute():
    expected_groups = [
        (0, 61),
        (58815, 1),
        (62687, 1),
        (103303, 1),
        (111999, 1),
        (117600, 1),
        (118010, 1),
        (125375, 8),
        (125623, 1),
        (127877, 1),
        (127891, 1),
        (128000, 9),
        (128065, 1),
        (128349, 1),
        (137010, 1),
    ]
    with get_provider() as provider:
        assert not provider.get_grouping()
        provider.set_groups("audio_bit_rate")
        assert len(provider.get_view_indices()) == 61
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 3
        for i, (value, count) in enumerate(((0, 61), (125375, 8), (128000, 9))):
            group = group_def["groups"][i]
            assert group["value"] == value
            assert group["count"] == count

        provider.set_groups("audio_bit_rate", allow_singletons=True)
        assert len(provider.get_view_indices()) == 61
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 15
        for i, (value, count) in enumerate(expected_groups):
            group = group_def["groups"][i]
            assert group["value"] == value
            assert group["count"] == count

        provider.set_groups("audio_bit_rate", reverse=True, allow_singletons=True)
        assert len(provider.get_view_indices()) == 1
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 15
        for i, (value, count) in enumerate(reversed(expected_groups)):
            group = group_def["groups"][i]
            assert group["value"] == value
            assert group["count"] == count

        provider.set_groups("audio_bit_rate", sorting="count", reverse=True)
        assert len(provider.get_view_indices()) == 61
        group_def = provider.get_group_def()
        for i, (value, count) in enumerate(((0, 61), (128000, 9), (125375, 8))):
            group = group_def["groups"][i]
            assert group["value"] == value
            assert group["count"] == count
            provider.set_group(i)
            assert len(provider.get_view_indices()) == count

        provider.set_sources([["readable", "without_thumbnails"]])
        provider.set_groups("audio_bit_rate", True, sorting="count", reverse=True)
        provider.set_group(0)
        assert len(provider.get_view_indices()) == 0


def test_provider_grouping_by_property():
    expected_without_singletons = [
        ("9", 2),
        ("a", 3),
        ("e", 3),
        ("sunshine", 2),
        ("unknown audio codec", 61),
        ("vertical", 7),
    ]
    with get_provider() as provider:
        provider.set_groups("category", True)
        assert len(provider.get_view_indices()) == 2
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 6
        for i, (value, count) in enumerate(expected_without_singletons):
            group = group_def["groups"][i]
            assert group["value"] == value
            assert group["count"] == count

        provider.set_groups("category", True, allow_singletons=True)
        assert len(provider.get_view_indices()) == 1
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 110
        ids_no_single = {86: 0, 97: 1, 103: 2, 106: 3, 107: 4, 108: 5}
        nb_found_no_single = 0
        for i, group in enumerate(group_def["groups"]):
            if i in ids_no_single:
                value, count = expected_without_singletons[ids_no_single[i]]
                assert group["value"] == value
                assert group["count"] == count
                nb_found_no_single += 1
            else:
                assert group["count"] == 1
        assert nb_found_no_single == len(expected_without_singletons)

        provider.set_groups("category", True, sorting="length")
        assert len(provider.get_view_indices()) == 2
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 6
        for i, (value, count) in enumerate(
            sorted(expected_without_singletons, key=lambda c: (len(c[0]), c[0]))
        ):
            group = group_def["groups"][i]
            assert group["value"] == value
            assert group["count"] == count

        provider.set_groups("category", True, sorting="length", reverse=True)
        assert len(provider.get_view_indices()) == 61
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 6
        for i, (value, count) in enumerate(
            sorted(
                expected_without_singletons,
                key=lambda c: (len(c[0]), c[0]),
                reverse=True,
            )
        ):
            group = group_def["groups"][i]
            assert group["value"] == value
            assert group["count"] == count

        provider.set_groups("category", True, sorting="count")
        assert len(provider.get_view_indices()) == 2
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 6
        for i, (value, count) in enumerate(
            sorted(expected_without_singletons, key=lambda c: (c[1], c[0]))
        ):
            group = group_def["groups"][i]
            assert group["value"] == value
            assert group["count"] == count

        provider.set_groups("category", True, sorting="count", reverse=True)
        assert len(provider.get_view_indices()) == 61
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 6
        for i, (value, count) in enumerate(
            sorted(
                expected_without_singletons, key=lambda c: (c[1], c[0]), reverse=True
            )
        ):
            group = group_def["groups"][i]
            assert group["value"] == value
            assert group["count"] == count


def test_provider_classifier():
    with get_provider() as provider:
        # provider._database.db.debug = True
        provider.set_groups(
            "category", True, sorting="count", reverse=True, allow_singletons=True
        )
        provider.set_classifier_path(["vertical"])
        assert len(provider.get_view_indices()) == 7
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 24
        group_0 = group_def["groups"][0]
        group_1 = group_def["groups"][1]
        group_2 = group_def["groups"][2]
        assert group_0["value"] is None
        assert group_0["count"] == 7
        assert group_1["value"] == "unknown audio codec"
        assert group_1["count"] == 7
        assert group_2["value"] == "e"
        assert group_2["count"] == 3

        provider.set_group(14)
        assert len(provider.get_view_indices()) == 1
        group_14 = group_def["groups"][14]
        assert group_14["value"] == "68233"
        assert group_14["count"] == 1

        provider.set_classifier_path(["vertical", "e"])
        provider.set_group(0)
        assert len(provider.get_view_indices()) == 3
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 10
        assert group_def["groups"][0]["value"] is None
        assert group_def["groups"][0]["count"] == 3

        provider.set_classifier_path(["vertical", "e", "does not exist"])
        provider.set_group(0)
        assert len(provider.get_view_indices()) == 0


def test_edit_properties():
    collection = get_collection()
    provider = collection.provider
    with provider:
        provider.set_search("palm beach", "and")
        assert provider.get_view_indices() == [84, 21]
        old_values = collection.get_all_prop_values("category", [84])[84]
        assert len(old_values) == 1
        new_values = list(old_values) + ["beach palm"]

        provider.set_search("palm beach", "exact")
        assert provider.get_view_indices() == [21]

        collection.set_video_prop_values("category", {84: new_values})
        assert collection.get_all_prop_values("category", [84])[84] == new_values
        provider.refresh()
        assert provider.get_view_indices() == [84, 21]

        collection.set_video_prop_values("category", {84: old_values})
        assert collection.get_all_prop_values("category", [84])[84] == old_values
        provider.refresh()
        assert provider.get_view_indices() == [21]


def test_search():
    with get_provider() as provider:
        provider.set_search("1", "id")
        assert len(provider.get_view_indices()) == 1

        # provider._database.db.debug = True
        provider.set_search("unknown", "and")
        assert len(provider.get_view_indices()) == 61
        provider.set_search("unknown", "or")
        assert len(provider.get_view_indices()) == 61
        provider.set_search("unknown", "exact")
        assert len(provider.get_view_indices()) == 61

        provider.set_search("unknown vertical", "and")
        assert len(provider.get_view_indices()) == 7
        provider.set_search("unknown vertical", "or")
        assert len(provider.get_view_indices()) == 61
        provider.set_search("unknown vertical", "exact")
        assert len(provider.get_view_indices()) == 0

        provider.set_search("palm beach", "and")
        assert len(provider.get_view_indices()) == 2
        provider.set_search("palm beach", "or")
        assert len(provider.get_view_indices()) == 3
        provider.set_search("palm beach", "exact")
        assert len(provider.get_view_indices()) == 1

        provider.set_search("then natural", "and")
        assert len(provider.get_view_indices()) == 3
        provider.set_search("then natural", "or")
        assert len(provider.get_view_indices()) == 4
        provider.set_search("then natural", "exact")
        assert len(provider.get_view_indices()) == 2

        provider.set_search("then.natural", "and")
        assert len(provider.get_view_indices()) == 3
        provider.set_search("then.natural", "or")
        assert len(provider.get_view_indices()) == 4
        provider.set_search("then.natural", "exact")
        assert len(provider.get_view_indices()) == 2

        provider.set_groups(
            "category", True, allow_singletons=1, reverse=True, sorting="count"
        )
        provider.set_search("then.natural", "and")
        assert len(provider.get_view_indices()) == 2
        provider.set_search("then.natural", "or")
        assert len(provider.get_view_indices()) == 3
        provider.set_search("then.natural", "exact")
        assert len(provider.get_view_indices()) == 1


def test_sorting():
    with get_provider() as provider:
        provider.set_sort(["-file_title"])
        indices = provider.get_view_indices()
        assert len(indices) == 90

        provider.set_sort(["file_title"])
        assert indices == list(reversed(provider.get_view_indices()))

        provider.set_sort(["date", "-file_title"])
        indices = provider.get_view_indices()
        assert len(indices) == 90

        provider.set_sort(["-date", "+file_title"])
        assert indices == list(reversed(provider.get_view_indices()))

        provider.set_groups("category", True, sorting="count", reverse=True)
        provider.set_sort(["file_title"])
        indices = provider.get_view_indices()
        assert len(indices) == 61

        provider.set_sort(["-file_title"])
        assert indices == list(reversed(provider.get_view_indices()))


def _test_provider_sorting_by_title_and_numeric():
    with get_provider() as provider:
        db = provider._database

        provider.set_sort(["file_title"])
        indices = provider.get_view_indices()
        ft_indices = db.get_videos(include=["file_title"], where={"video_id": indices})

        provider.set_sort(["file_title_numeric"])
        indices_about_numeric = provider.get_view_indices()
        ft_indices_about_numeric = db.get_videos(
            include=["file_title"], where={"video_id": indices_about_numeric}
        )

        assert ft_indices == ft_indices_about_numeric


def test_update():
    collection = get_collection()
    # collection.db.debug = True
    collection.refresh()


def test_prop_types_default_value():
    collection = get_collection()
    properties = collection.get_prop_types()
    assert len(properties) == 6
    assert properties == [
        {
            "defaultValues": [0.0],
            "enumeration": None,
            "multiple": 0,
            "name": "appreciation",
            "property_id": 0,
            "type": "float",
        },
        {
            "defaultValues": [],
            "enumeration": None,
            "multiple": 1,
            "name": "category",
            "property_id": 1,
            "type": "str",
        },
        {
            "defaultValues": [False],
            "enumeration": None,
            "multiple": 0,
            "name": "has sky",
            "property_id": 2,
            "type": "bool",
        },
        {
            "defaultValues": [0],
            "enumeration": [0, 1],
            "multiple": 0,
            "name": "is nature",
            "property_id": 3,
            "type": "int",
        },
        {
            "defaultValues": [0],
            "enumeration": None,
            "multiple": 0,
            "name": "number of animals",
            "property_id": 4,
            "type": "int",
        },
        {
            "defaultValues": ["example video"],
            "enumeration": None,
            "multiple": 0,
            "name": "title",
            "property_id": 5,
            "type": "str",
        },
    ]


def test_get_videos():
    collection = get_collection()
    indices = list(reversed(range(20)))
    videos = collection.get_videos(include=(), where={"video_id": indices})
    assert len(videos) == len(indices)
    for video, video_id in zip(videos, indices):
        assert video["video_id"] == video_id
