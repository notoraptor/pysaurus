"""
Tests for database providers using example_db_in_pysaurus (90 videos).

These tests verify that AbstractVideoProvider methods work correctly
on both JSON and Saurus SQL database implementations.
"""

import pytest

from pysaurus.database.abstract_database import AbstractDatabase


@pytest.fixture(params=["json", "saurus_sql"])
def disk_database(
    request, example_json_database, example_saurus_database
) -> AbstractDatabase:
    """Parametrized fixture for read-only database access."""
    if request.param == "json":
        return example_json_database
    else:
        return example_saurus_database


@pytest.fixture(params=["json", "saurus_sql"])
def memory_database(
    request, example_json_database_memory, example_saurus_database_memory
) -> AbstractDatabase:
    """Parametrized fixture for in-memory database access (for write tests)."""
    if request.param == "json":
        return example_json_database_memory
    else:
        return example_saurus_database_memory


class TestDatabaseProvider:
    """Tests for AbstractVideoProvider methods (read-only)."""

    @pytest.fixture
    def provider(self, disk_database):
        return disk_database.provider

    def test_provider(self, provider):
        indices = provider.get_view_indices()
        assert len(indices) == 90

    def test_provider_sources(self, provider):
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

    def test_provider_grouping_by_attribute(self, provider):
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

    def test_provider_grouping_by_property(self, provider):
        expected_without_singletons = [
            ("9", 2),
            ("a", 3),
            ("e", 3),
            ("sunshine", 2),
            ("unknown audio codec", 61),
            ("vertical", 7),
        ]
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

    def test_provider_classifier(self, provider):
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

    def test_search(self, provider):
        provider.set_search("196", "id")
        assert len(provider.get_view_indices()) == 1

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
        assert len(provider.get_view_indices()) == 1

        provider.set_search("then.natural", "and")
        assert len(provider.get_view_indices()) == 3
        provider.set_search("then.natural", "or")
        assert len(provider.get_view_indices()) == 4
        provider.set_search("then.natural", "exact")
        assert len(provider.get_view_indices()) == 1

        provider.set_groups(
            "category", True, allow_singletons=1, reverse=True, sorting="count"
        )
        provider.set_search("then.natural", "and")
        assert len(provider.get_view_indices()) == 2
        provider.set_search("then.natural", "or")
        assert len(provider.get_view_indices()) == 3
        provider.set_search("then.natural", "exact")
        assert len(provider.get_view_indices()) == 1

    def test_sorting(self, provider):
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

    def test_get_videos(self, disk_database):
        indices = [196, 114]
        videos = disk_database.get_videos(include=(), where={"video_id": indices})
        assert len(videos) == len(indices)
        for video, video_id in zip(videos, indices):
            assert video.video_id == video_id


class TestDatabaseWriteOperations:
    """Tests for database write operations (using in-memory copies)."""

    def test_edit_properties(self, memory_database):
        provider = memory_database.provider
        provider.set_search("palm beach", "and")
        assert provider.get_view_indices() == [196, 114]
        old_values = memory_database.videos_tag_get("category", [196])[196]
        assert len(old_values) == 1
        new_values = list(old_values) + ["palm beach"]

        provider.set_search("palm beach", "exact")
        # Right now only video 114 is associated to category "palm beach"
        assert provider.get_view_indices() == [114]

        memory_database.videos_tag_set("category", {196: new_values})
        assert memory_database.videos_tag_get("category", [196])[196] == new_values
        provider.refresh()
        search = provider.get_search()
        assert search.text == "palm beach"
        assert search.cond == "exact"
        # With video 196 now associated with the category "palm beach",
        # we should get 2 videos in view
        assert provider.get_view_indices() == [196, 114]

        memory_database.videos_tag_set("category", {196: old_values})
        assert memory_database.videos_tag_get("category", [196])[196] == old_values
        provider.refresh()
        search = provider.get_search()
        assert search.text == "palm beach"
        assert search.cond == "exact"
        # With video 196 back to its old categories, we should get 1 video again.
        assert provider.get_view_indices() == [114]

    def test_refresh(self, memory_database):
        memory_database.refresh()
