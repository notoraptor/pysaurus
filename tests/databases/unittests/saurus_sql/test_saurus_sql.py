"""
Tests for database providers using example_db_in_pysaurus (90 videos).

These tests verify that video querying and write operations work correctly
on the Saurus SQL database implementation.
"""

import pprint

import pytest

from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.dbview.view_context import ViewContext
from pysaurus.interface.common.common import FIELD_MAP


@pytest.fixture
def disk_database(example_saurus_database) -> AbstractDatabase:
    """Read-only Saurus SQL database."""
    return example_saurus_database


@pytest.fixture
def memory_database(example_saurus_database_memory) -> AbstractDatabase:
    """In-memory Saurus SQL database for write tests."""
    return example_saurus_database_memory


class TestDatabaseProvider:
    """Tests for video querying methods (read-only)."""

    def _query_ids(self, db, view) -> list[int]:
        return [v.video_id for v in db.query_videos(view, None, None).result]

    def _query_stats(self, db, view):
        return db.query_videos(view, 1, 0).classifier_stats

    def test_provider(self, disk_database):
        view = ViewContext()
        indices = self._query_ids(disk_database, view)
        assert len(indices) == 90

    def test_provider_sources(self, disk_database):
        view = ViewContext()
        assert len(self._query_ids(disk_database, view)) == 90

        view.set_sources([["not_found"]])
        assert len(self._query_ids(disk_database, view)) == 3

        view.set_sources([["found"]])
        assert len(self._query_ids(disk_database, view)) == 90

        view.set_sources([["unreadable"]])
        assert len(self._query_ids(disk_database, view)) == 3

        view.set_sources([["readable", "without_thumbnails"]])
        assert len(self._query_ids(disk_database, view)) == 0

        view.set_sources([["readable", "with_thumbnails"]])
        assert len(self._query_ids(disk_database, view)) == 90

        view.set_sources([["unreadable"], ["readable"]])
        assert len(self._query_ids(disk_database, view)) == 93

    def test_provider_grouping_by_attribute(self, disk_database):
        db = disk_database
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
        view = ViewContext()
        assert not view.grouping.field

        view.set_grouping("audio_bit_rate")
        assert len(self._query_ids(db, view)) == 61
        stats = self._query_stats(db, view)
        assert len(stats) == 3
        for i, (value, count) in enumerate(((0, 61), (125375, 8), (128000, 9))):
            assert stats[i].value == value
            assert stats[i].count == count

        view.set_grouping("audio_bit_rate", allow_singletons=True)
        assert len(self._query_ids(db, view)) == 61
        stats = self._query_stats(db, view)
        assert len(stats) == 15
        for i, (value, count) in enumerate(expected_groups):
            assert stats[i].value == value
            assert stats[i].count == count

        view.set_grouping("audio_bit_rate", reverse=True, allow_singletons=True)
        assert len(self._query_ids(db, view)) == 1
        stats = self._query_stats(db, view)
        assert len(stats) == 15
        for i, (value, count) in enumerate(reversed(expected_groups)):
            assert stats[i].value == value
            assert stats[i].count == count

        view.set_grouping("audio_bit_rate", sorting="count", reverse=True)
        stats = self._query_stats(db, view)
        for i, (value, count) in enumerate(((0, 61), (128000, 9), (125375, 8))):
            assert stats[i].value == value
            assert stats[i].count == count
            view.set_group(i)
            assert len(self._query_ids(db, view)) == count

        view.set_sources([["readable", "without_thumbnails"]])
        view.set_grouping(
            "audio_bit_rate", is_property=True, sorting="count", reverse=True
        )
        view.set_group(0)
        assert len(self._query_ids(db, view)) == 0

    @pytest.mark.parametrize("attribute", [field.name for field in FIELD_MAP.allowed])
    def test_provider_grouping_by_attributes(
        self, disk_database, attribute, data_regression
    ):
        db = disk_database
        field = FIELD_MAP.fields[attribute]
        view = ViewContext()
        view.set_grouping(attribute, allow_singletons=not field.is_only_many())
        nb_videos_first_group = len(self._query_ids(db, view))
        result = db.query_videos(view, 1, 0)
        group_def = view.grouping.to_dict(
            group_id=result.group_id,
            groups=[
                {"value": _serializable(s.value), "count": s.count}
                for s in result.classifier_stats
            ],
        )
        results = {
            "nb_videos_first_group": nb_videos_first_group,
            "group_def": group_def,
        }
        pprint.pprint(results)
        data_regression.check(results)

    def test_provider_grouping_by_property(self, disk_database):
        db = disk_database
        expected_without_singletons = [
            ("9", 2),
            ("a", 3),
            ("e", 3),
            ("sunshine", 2),
            ("unknown audio codec", 61),
            ("vertical", 7),
        ]
        view = ViewContext()

        view.set_grouping("category", is_property=True)
        assert len(self._query_ids(db, view)) == 2
        stats = self._query_stats(db, view)
        assert len(stats) == 6
        for i, (value, count) in enumerate(expected_without_singletons):
            assert stats[i].value == value
            assert stats[i].count == count

        view.set_grouping("category", is_property=True, allow_singletons=True)
        assert len(self._query_ids(db, view)) == 1
        stats = self._query_stats(db, view)
        assert len(stats) == 110
        ids_no_single = {86: 0, 97: 1, 103: 2, 106: 3, 107: 4, 108: 5}
        nb_found_no_single = 0
        for i, s in enumerate(stats):
            if i in ids_no_single:
                value, count = expected_without_singletons[ids_no_single[i]]
                assert s.value == value
                assert s.count == count
                nb_found_no_single += 1
            else:
                assert s.count == 1
        assert nb_found_no_single == len(expected_without_singletons)

        view.set_grouping("category", is_property=True, sorting="length")
        assert len(self._query_ids(db, view)) == 2
        stats = self._query_stats(db, view)
        assert len(stats) == 6
        for i, (value, count) in enumerate(
            sorted(expected_without_singletons, key=lambda c: (len(c[0]), c[0]))
        ):
            assert stats[i].value == value
            assert stats[i].count == count

        view.set_grouping("category", is_property=True, sorting="length", reverse=True)
        assert len(self._query_ids(db, view)) == 61
        stats = self._query_stats(db, view)
        assert len(stats) == 6
        for i, (value, count) in enumerate(
            sorted(
                expected_without_singletons,
                key=lambda c: (len(c[0]), c[0]),
                reverse=True,
            )
        ):
            assert stats[i].value == value
            assert stats[i].count == count

        view.set_grouping("category", is_property=True, sorting="count")
        assert len(self._query_ids(db, view)) == 2
        stats = self._query_stats(db, view)
        assert len(stats) == 6
        for i, (value, count) in enumerate(
            sorted(expected_without_singletons, key=lambda c: (c[1], c[0]))
        ):
            assert stats[i].value == value
            assert stats[i].count == count

        view.set_grouping("category", is_property=True, sorting="count", reverse=True)
        assert len(self._query_ids(db, view)) == 61
        stats = self._query_stats(db, view)
        assert len(stats) == 6
        for i, (value, count) in enumerate(
            sorted(
                expected_without_singletons, key=lambda c: (c[1], c[0]), reverse=True
            )
        ):
            assert stats[i].value == value
            assert stats[i].count == count

    def test_provider_classifier(self, disk_database):
        db = disk_database
        view = ViewContext()
        view.set_grouping(
            "category",
            is_property=True,
            sorting="count",
            reverse=True,
            allow_singletons=True,
        )
        view.classifier = ["vertical"]
        assert len(self._query_ids(db, view)) == 7
        stats = self._query_stats(db, view)
        assert len(stats) == 24
        assert stats[0].value is None
        assert stats[0].count == 7
        assert stats[1].value == "unknown audio codec"
        assert stats[1].count == 7
        assert stats[2].value == "e"
        assert stats[2].count == 3

        view.set_group(14)
        assert len(self._query_ids(db, view)) == 1
        assert stats[14].value == "68233"
        assert stats[14].count == 1

        view.classifier = ["vertical", "e"]
        view.set_group(0)
        assert len(self._query_ids(db, view)) == 3
        stats = self._query_stats(db, view)
        assert len(stats) == 10
        assert stats[0].value is None
        assert stats[0].count == 3

        view.classifier = ["vertical", "e", "does not exist"]
        view.set_group(0)
        assert len(self._query_ids(db, view)) == 0

    def test_search(self, disk_database):
        db = disk_database
        view = ViewContext()

        view.set_search("196", "id")
        assert len(self._query_ids(db, view)) == 1

        view.set_search("unknown", "and")
        assert len(self._query_ids(db, view)) == 61
        view.set_search("unknown", "or")
        assert len(self._query_ids(db, view)) == 61
        view.set_search("unknown", "exact")
        assert len(self._query_ids(db, view)) == 61

        view.set_search("unknown vertical", "and")
        assert len(self._query_ids(db, view)) == 7
        view.set_search("unknown vertical", "or")
        assert len(self._query_ids(db, view)) == 61
        view.set_search("unknown vertical", "exact")
        assert len(self._query_ids(db, view)) == 0

        view.set_search("palm beach", "and")
        assert len(self._query_ids(db, view)) == 2
        view.set_search("palm beach", "or")
        assert len(self._query_ids(db, view)) == 3
        view.set_search("palm beach", "exact")
        assert len(self._query_ids(db, view)) == 1

        view.set_search("then natural", "and")
        assert len(self._query_ids(db, view)) == 3
        view.set_search("then natural", "or")
        assert len(self._query_ids(db, view)) == 4
        view.set_search("then natural", "exact")
        assert len(self._query_ids(db, view)) == 1

        view.set_search("then.natural", "and")
        assert len(self._query_ids(db, view)) == 3
        view.set_search("then.natural", "or")
        assert len(self._query_ids(db, view)) == 4
        view.set_search("then.natural", "exact")
        assert len(self._query_ids(db, view)) == 1

        view.set_grouping(
            "category",
            is_property=True,
            allow_singletons=True,
            reverse=True,
            sorting="count",
        )
        view.set_search("then.natural", "and")
        assert len(self._query_ids(db, view)) == 2
        view.set_search("then.natural", "or")
        assert len(self._query_ids(db, view)) == 3
        view.set_search("then.natural", "exact")
        assert len(self._query_ids(db, view)) == 1

    def test_sorting(self, disk_database):
        db = disk_database
        view = ViewContext()

        view.set_sort(["-file_title"])
        indices = self._query_ids(db, view)
        assert len(indices) == 90

        view.set_sort(["file_title"])
        assert indices == list(reversed(self._query_ids(db, view)))

        view.set_sort(["date", "-file_title"])
        indices = self._query_ids(db, view)
        assert len(indices) == 90

        view.set_sort(["-date", "+file_title"])
        assert indices == list(reversed(self._query_ids(db, view)))

        view.set_grouping("category", is_property=True, sorting="count", reverse=True)
        view.set_sort(["file_title"])
        indices = self._query_ids(db, view)
        assert len(indices) == 61

        view.set_sort(["-file_title"])
        assert indices == list(reversed(self._query_ids(db, view)))

    def test_get_videos(self, disk_database, data_regression):
        indices = [196, 114]
        videos = disk_database.get_videos(
            include=None, where={"video_id": indices}, with_moves=True
        )
        assert len(videos) == len(indices)
        assert {v.video_id for v in videos} == set(indices)
        videos.sort(key=lambda v: v.video_id)
        data_regression.check([_to_dict(video) for video in videos])


def _serializable(value):
    """Convert a value to a YAML-serializable type."""
    if isinstance(value, (str, bool, int, float, type(None))):
        return value
    return str(value)


def _to_dict(v):
    d = {}
    for name in sorted(dir(v)):
        if (
            name[0] != "_"
            and name not in ["runtime"]
            and isinstance(getattr(type(v), name), property)
        ):
            value = getattr(v, name)
            d[name] = (
                value
                if isinstance(value, (str, bool, int, float, list, set, dict))
                else str(value)
            )
    return d


class TestDatabaseWriteOperations:
    """Tests for database write operations (using in-memory copies)."""

    def _query_ids(self, db, view) -> list[int]:
        return [v.video_id for v in db.query_videos(view, None, None).result]

    def test_edit_properties(self, memory_database):
        db = memory_database
        view = ViewContext()
        view.set_search("palm beach", "and")
        assert self._query_ids(db, view) == [196, 114]
        old_values = db.videos_tag_get("category", [196])[196]
        assert len(old_values) == 1
        new_values = list(old_values) + ["palm beach"]

        view.set_search("palm beach", "exact")
        # Right now only video 114 is associated to category "palm beach"
        assert self._query_ids(db, view) == [114]

        db.videos_tag_set("category", {196: new_values})
        assert db.videos_tag_get("category", [196])[196] == new_values
        assert view.search.text == "palm beach"
        assert view.search.cond == "exact"
        # With video 196 now associated with the category "palm beach",
        # we should get 2 videos in view
        assert self._query_ids(db, view) == [196, 114]

        db.videos_tag_set("category", {196: old_values})
        assert db.videos_tag_get("category", [196])[196] == old_values
        assert view.search.text == "palm beach"
        assert view.search.cond == "exact"
        # With video 196 back to its old categories, we should get 1 video again.
        assert self._query_ids(db, view) == [114]

    def test_refresh(self, memory_database):
        memory_database.algos.refresh()
