"""Tests for videroid's VideroidContext (the ViewModel) against an in-memory db.

Exercises the REAL VideroidContext (not a mock): the conftest injects a copy of
`test_database` into `context._api.database`. Assertions avoid hard-coded counts.
"""

import pytest

from pysaurus.application.exceptions import PysaurusError
from pysaurus.core.classes import Selector


class TestReadAccessors:
    def test_has_database(self, videroid_context):
        assert videroid_context.has_database()

    def test_has_database_false_without_db(self, videroid_context):
        videroid_context._api.database = None
        assert not videroid_context.has_database()

    def test_get_database_name(self, videroid_context):
        assert videroid_context.get_database_name()


class TestGetVideos:
    def test_returns_search_context(self, videroid_context):
        result = videroid_context.get_videos(10, 0)
        assert result is not None
        assert result.view_count > 0
        assert len(result.result) <= 10

    def test_pagination_disjoint(self, videroid_context):
        full = videroid_context.get_videos(1000, 0)
        if full.view_count > 5:
            page0 = videroid_context.get_videos(5, 0)
            page1 = videroid_context.get_videos(5, 1)
            assert len(page0.result) == 5
            ids0 = {v.video_id for v in page0.result}
            ids1 = {v.video_id for v in page1.result}
            assert ids0.isdisjoint(ids1)

    def test_none_without_db(self, videroid_context):
        videroid_context._api.database = None
        assert videroid_context.get_videos(10, 0) is None


class TestGetAllViewIds:
    def test_returns_every_view_id(self, videroid_context):
        full = videroid_context.get_videos(1000, 0)
        ids = videroid_context.get_all_view_ids()
        assert len(ids) == full.view_count
        assert all(isinstance(i, int) for i in ids)

    def test_empty_without_db(self, videroid_context):
        videroid_context._api.database = None
        assert videroid_context.get_all_view_ids() == []


class TestFilters:
    def test_search_narrows_then_clears(self, videroid_context):
        full = videroid_context.get_videos(1000, 0).view_count
        videroid_context.set_search("zzz_no_such_term_zzz", "and")
        # A term present in no video must yield exactly zero matches (a no-op
        # search would wrongly keep `full` here).
        assert videroid_context.get_videos(1000, 0).view_count == 0
        videroid_context.set_search("", "and")
        assert videroid_context.get_videos(1000, 0).view_count == full

    def test_sorting_orders_by_date(self, videroid_context):
        videroid_context.set_sorting(["-date"])
        desc = [v.date for v in videroid_context.get_videos(1000, 0).result]
        assert desc == sorted(desc, reverse=True)  # really date-descending
        videroid_context.set_sorting(["+date"])
        asc = [v.date for v in videroid_context.get_videos(1000, 0).result]
        assert asc == sorted(asc)  # and ascending the other way

    def test_grouping_creates_groups_then_clears(self, videroid_context):
        ctx = videroid_context
        db = ctx._api.database
        ctx.create_prop_type("g", "str", "", True)  # controlled grouping
        vid = ctx.get_videos(1, 0).result[0].video_id
        with db.to_save():
            db.videos_tag_set("g", {vid: ["v1"]})
        ctx.set_groups("g", is_property=True)
        grouped = ctx.get_videos(1000, 0)
        assert grouped.grouping is not None and grouped.grouping.field == "g"
        assert grouped.classifier_stats  # at least the "v1" group exists
        ctx.clear_groups()
        cleared = ctx.get_videos(1000, 0)
        assert cleared.grouping is None or cleared.grouping.field is None


class TestSourceExpression:
    """set_source_expression validates against the real DB (mirrors kyuti)."""

    def test_valid_expression_roundtrips(self, videroid_context):
        videroid_context.set_source_expression("  width > 0  ")
        assert videroid_context.get_source_expression() == "width > 0"  # stripped

    def test_invalid_expression_raises_and_keeps_state(self, videroid_context):
        videroid_context.set_source_expression("width > 0")
        with pytest.raises(PysaurusError):
            videroid_context.set_source_expression("this is )( not valid (((")
        # The bad expression was rejected BEFORE storing -> state unchanged.
        assert videroid_context.get_source_expression() == "width > 0"

    def test_no_db_set_is_noop(self, videroid_context):
        videroid_context.set_source_expression("width > 0")
        videroid_context._api.database = None
        videroid_context.set_source_expression("height > 0")  # guarded -> no-op
        assert videroid_context.get_source_expression() == "width > 0"


class TestPropertyTypes:
    def test_get_prop_types_contains_category(self, videroid_context):
        props = videroid_context.get_prop_types()
        assert isinstance(props, list)
        assert "category" in {p.name for p in props}

    def test_create_rename_delete_roundtrip(self, videroid_context):
        videroid_context.create_prop_type("vtest", "str", "", False)
        assert "vtest" in {p.name for p in videroid_context.get_prop_types()}
        videroid_context.rename_prop_type("vtest", "vtest2")
        names = {p.name for p in videroid_context.get_prop_types()}
        assert "vtest2" in names and "vtest" not in names
        videroid_context.delete_prop_type("vtest2")
        assert "vtest2" not in {p.name for p in videroid_context.get_prop_types()}

    def test_get_property_values_reflects_tags(self, videroid_context):
        ctx = videroid_context
        db = ctx._api.database
        ctx.create_prop_type("g", "str", "", True)
        vid = ctx.get_videos(1, 0).result[0].video_id
        with db.to_save():
            db.videos_tag_set("g", {vid: ["hello"]})
        values = ctx.get_property_values("g")  # dict[video_id, list[value]]
        assert values.get(vid) == ["hello"]


class TestCallOnView:
    def test_count_property_values(self, videroid_context):
        ctx = videroid_context
        db = ctx._api.database
        ctx.create_prop_type("g", "str", "", True)
        vid = ctx.get_videos(1, 0).result[0].video_id
        with db.to_save():
            db.videos_tag_set("g", {vid: ["hello"]})
        selector = Selector(True, set()).to_dict()
        result = ctx.call_on_view(selector, "count_property_values", "g")
        # sorted list of [value, count] pairs -> "hello" tagged on exactly 1 video
        assert [pair for pair in result if pair[0] == "hello"] == [["hello", 1]]

    def test_none_without_db(self, videroid_context):
        videroid_context._api.database = None
        selector = Selector(True, set()).to_dict()
        assert (
            videroid_context.call_on_view(selector, "count_property_values", "category")
            is None
        )


class TestVideoActions:
    def test_delete_video_entry(self, videroid_context):
        before = videroid_context.get_videos(1000, 0)
        videroid_context.delete_video_entry(before.result[0].video_id)
        after = videroid_context.get_videos(1000, 0)
        assert after.view_count == before.view_count - 1

    def test_delete_video_entries_batch(self, videroid_context):
        before = videroid_context.get_videos(1000, 0)
        if before.view_count >= 2:
            ids = [before.result[0].video_id, before.result[1].video_id]
            videroid_context.delete_video_entries(ids)
            after = videroid_context.get_videos(1000, 0)
            assert after.view_count == before.view_count - 2


class TestScanResult:
    def test_drop_scanned_paths_noop_without_scan(self, videroid_context):
        assert videroid_context.get_last_scan_result() is None
        videroid_context.drop_scanned_paths({"whatever"})
        assert videroid_context.get_last_scan_result() is None
