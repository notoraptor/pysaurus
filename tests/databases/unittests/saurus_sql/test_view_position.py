"""Tests for AbstractDatabase.get_view_position (nearest value in sorted view)."""

import pytest

from pysaurus.core.classes import Selector
from pysaurus.dbview.view_context import ViewContext


def _lengths(db, view) -> list[float]:
    return [v.length.t / 1_000_000 for v in db.query_videos(view, None, None).result]


class TestGetViewPosition:
    def test_ascending_targets_first_of_equal_run(self, example_saurus_database):
        db = example_saurus_database
        view = ViewContext()
        view.set_sort(["+length"])
        lengths = _lengths(db, view)
        assert len(lengths) == 90
        assert lengths == sorted(lengths)
        for length in set(lengths):
            assert db.get_view_position(view, "length", length) == lengths.index(length)

    def test_descending_targets_last_of_equal_run(self, example_saurus_database):
        db = example_saurus_database
        view = ViewContext()
        view.set_sort(["-length"])
        lengths = _lengths(db, view)
        assert lengths == sorted(lengths, reverse=True)
        for length in set(lengths):
            expected = len(lengths) - 1 - lengths[::-1].index(length)
            assert db.get_view_position(view, "length", length) == expected

    def test_nearest_between_two_values(self, example_saurus_database):
        db = example_saurus_database
        view = ViewContext()
        view.set_sort(["+length"])
        lengths = _lengths(db, view)
        distinct = sorted(set(lengths))
        lower, upper = distinct[len(distinct) // 2], distinct[len(distinct) // 2 + 1]
        assert db.get_view_position(view, "length", lower + 0.1) == lengths.index(lower)
        assert db.get_view_position(view, "length", upper - 0.1) == lengths.index(upper)
        # Exact tie: the upper neighbour wins.
        assert db.get_view_position(
            view, "length", (lower + upper) / 2
        ) == lengths.index(upper)

    def test_outside_range_clamps_to_ends(self, example_saurus_database):
        db = example_saurus_database
        view = ViewContext()
        view.set_sort(["+length"])
        lengths = _lengths(db, view)
        assert db.get_view_position(view, "length", -5) == 0
        last = lengths[-1]
        assert db.get_view_position(view, "length", last + 1e9) == lengths.index(last)

    def test_secondary_sort_keys_are_allowed(self, example_saurus_database):
        db = example_saurus_database
        view = ViewContext()
        view.set_sort(["+length", "-title"])
        lengths = _lengths(db, view)
        target = lengths[10]
        assert db.get_view_position(view, "length", target) == lengths.index(target)

    def test_selector_restricts_the_view(self, example_saurus_database):
        db = example_saurus_database
        view = ViewContext()
        view.set_sort(["+length"])
        videos = db.query_videos(view, None, None).result
        kept = {v.video_id for v in videos[::2]}
        selector = Selector(False, kept)
        lengths = [v.length.t / 1_000_000 for v in videos if v.video_id in kept]
        for length in set(lengths):
            assert db.get_view_position(
                view, "length", length, selector
            ) == lengths.index(length)

    def test_empty_view_returns_none(self, example_saurus_database):
        db = example_saurus_database
        view = ViewContext()
        view.set_sort(["+length"])
        view.set_search("zzzz no such video zzzz", "exact")
        assert db.query_videos(view, None, None).result == []
        assert db.get_view_position(view, "length", 60) is None

    def test_requires_length_as_first_sort_key(self, example_saurus_database):
        db = example_saurus_database
        view = ViewContext()
        with pytest.raises(ValueError):
            db.get_view_position(view, "length", 60)
        view.set_sort(["+title", "+length"])
        with pytest.raises(ValueError):
            db.get_view_position(view, "length", 60)
