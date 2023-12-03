"""
NB: One can put tests in a class, with class name starting with "Test
and testing method names starting with "test_". but this class must
not have a __init__ method:
https://docs.pytest.org/en/7.1.x/explanation/goodpractices.html#test-discovery
"""
from saurus.sql.pysaurus_program import PysaurusProgram


def get_collection():
    name = "example_db_in_pysaurus"
    program = PysaurusProgram()
    return program.open_database(name)


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
        assert len(provider.get_view_indices()) == 0

        provider.set_sources([["found"]])
        assert len(provider.get_view_indices()) == 93

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
            given_value = group["value"][0]
            given_count = group["count"]
            assert given_value == value
            assert given_count == count

        provider.set_groups("audio_bit_rate", allow_singletons=True)
        assert len(provider.get_view_indices()) == 61
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 15
        for i, (value, count) in enumerate(expected_groups):
            group = group_def["groups"][i]
            given_value = group["value"][0]
            given_count = group["count"]
            assert given_value == value
            assert given_count == count

        provider.set_groups("audio_bit_rate", reverse=True, allow_singletons=True)
        assert len(provider.get_view_indices()) == 1
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 15
        for i, (value, count) in enumerate(reversed(expected_groups)):
            group = group_def["groups"][i]
            given_value = group["value"][0]
            given_count = group["count"]
            assert given_value == value
            assert given_count == count
