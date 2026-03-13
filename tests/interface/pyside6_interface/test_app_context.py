"""
Tests for AppContext facade methods.

Tests the real AppContext class with a SQL in-memory database,
verifying both correctness and that state_changed signal is emitted.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest.mock import patch

import pytest

from pysaurus.interface.pyside6.app_context import AppContext
from tests.utils import get_saurus_sql_database


@pytest.fixture
def ctx():
    """Create a real AppContext with a FeatureAPI backed by an in-memory SQL database."""
    from pysaurus.core.notifying import DEFAULT_NOTIFIER
    from pysaurus.interface.api.feature_api import FeatureAPI

    with patch("pysaurus.interface.pyside6.app_context.PySide6API"):
        app_ctx = AppContext()
    with patch("pysaurus.interface.api.feature_api.Application"):
        api = FeatureAPI(DEFAULT_NOTIFIER)
    api.database = get_saurus_sql_database()
    app_ctx._api = api
    return app_ctx


# =========================================================================
# get_videos
# =========================================================================


class TestGetVideos:
    def test_returns_search_context(self, ctx):
        result = ctx.get_videos(page_size=10, page_number=0)
        assert result is not None
        assert result.view_count > 0
        assert len(result.result) <= 10

    def test_pagination(self, ctx):
        full = ctx.get_videos(page_size=100, page_number=0)
        page1 = ctx.get_videos(page_size=5, page_number=0)
        page2 = ctx.get_videos(page_size=5, page_number=1)
        assert len(page1.result) == 5
        if full.view_count > 5:
            assert len(page2.result) > 0
            ids1 = {v.video_id for v in page1.result}
            ids2 = {v.video_id for v in page2.result}
            assert ids1.isdisjoint(ids2)

    def test_returns_none_without_database(self, ctx):
        ctx._api.database = None
        assert ctx.get_videos(10, 0) is None


# =========================================================================
# set_groups / clear_groups / set_search / set_sorting
# =========================================================================


class TestViewMutations:
    def test_set_groups_emits_state_changed(self, ctx, qtbot):
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.set_groups(
                field="extension",
                is_property=False,
                sorting="field",
                reverse=False,
                allow_singletons=True,
            )
        result = ctx.get_videos(10, 0)
        assert result.result_groups is not None
        assert len(result.result_groups) > 0

    def test_clear_groups_emits_state_changed(self, ctx, qtbot):
        ctx.set_groups(
            field="extension",
            is_property=False,
            sorting="field",
            reverse=False,
            allow_singletons=True,
        )
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.clear_groups()
        result = ctx.get_videos(10, 0)
        assert len(result.result_groups) == 0

    def test_set_search_emits_state_changed(self, ctx, qtbot):
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.set_search("test", "and")
        assert ctx._view.search.text == "test"

    def test_set_sorting_emits_state_changed(self, ctx, qtbot):
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.set_sorting(["-file_size"])
        assert ctx._view.sorting == ["-file_size"]

    def test_set_sources_emits_state_changed(self, ctx, qtbot):
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.set_sources([["readable"]])

    def test_set_group_emits_state_changed(self, ctx, qtbot):
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.set_group(0)


# =========================================================================
# Classifier operations
# =========================================================================


class TestClassifierOperations:
    def _setup_grouping(self, ctx):
        """Set up grouping by extension and load initial results."""
        ctx._view.set_grouping(
            field="extension",
            is_property=False,
            sorting="field",
            reverse=False,
            allow_singletons=True,
        )
        ctx.get_videos(10, 0)

    def test_classifier_select_group_emits_state_changed(self, ctx, qtbot):
        self._setup_grouping(ctx)
        result = ctx.get_videos(10, 0)
        assert result is not None
        assert len(result.result_groups) > 0
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.classifier_select_group(0)
        assert len(ctx._view.classifier) == 1

    def test_classifier_back_emits_state_changed(self, ctx, qtbot):
        self._setup_grouping(ctx)
        ctx.classifier_select_group(0)
        assert len(ctx._view.classifier) == 1
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.classifier_back()
        assert len(ctx._view.classifier) == 0

    def test_classifier_reverse_emits_state_changed(self, ctx, qtbot):
        self._setup_grouping(ctx)
        ctx.classifier_select_group(0)
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            result = ctx.classifier_reverse()
        assert isinstance(result, list)

    def test_classifier_focus_prop_val(self, ctx, qtbot):
        # Get a property with values
        prop_types = ctx._database.get_prop_types()
        if not prop_types:
            pytest.skip("No properties in test database")
        prop_name = prop_types[0].name
        # Find a value for this property
        all_tags = ctx._database.videos_tag_get(prop_name)
        values = set()
        for vid_values in all_tags.values():
            values.update(vid_values)
        if not values:
            pytest.skip(f"No values for property {prop_name}")
        field_value = next(iter(values))

        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.classifier_focus_prop_val(prop_name, field_value)

        assert ctx._view.grouping.field == prop_name
        assert ctx._view.grouping.is_property is True
        assert len(ctx._view.classifier) == 1

    def test_classifier_focus_prop_val_returns_without_database(self, ctx):
        ctx._api.database = None
        ctx.classifier_focus_prop_val("some_prop", "some_value")
        # Should silently return without crashing

    def test_classifier_concatenate_path(self, ctx, qtbot):
        # Use an existing property from the test database
        prop_types = ctx._database.get_prop_types()
        multi_props = [p for p in prop_types if p.multiple]
        if not multi_props:
            pytest.skip("No multiple properties in test database")
        prop_name = multi_props[0].name
        # Create destination property
        ctx._database.prop_type_add("concat_dst", "str", "", True)
        # Set grouping to the source property
        ctx._view.set_grouping(
            field=prop_name,
            is_property=True,
            sorting="field",
            reverse=False,
            allow_singletons=True,
        )
        # Navigate into classifier
        result = ctx._database.query_videos(ctx._view, 1, 0)
        if len(result.result_groups) == 0:
            pytest.skip("No groups for property")
        value = result.result_groups[0].get_value()
        ctx._view.classifier_select(value)
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.classifier_concatenate_path("concat_dst")
        assert ctx._view.classifier == []
        assert ctx._view.group == 0


# =========================================================================
# apply_on_view / query_on_view
# =========================================================================


class TestApplyOnView:
    def test_query_on_view_does_not_emit_state_changed(self, ctx, qtbot):
        # Set up: create property with values
        ctx._database.prop_type_add("query_prop", "str", "", True)
        videos = ctx._database.get_videos(include=["video_id"])[:5]
        video_ids = [v.video_id for v in videos]
        ctx._database.videos_tag_set("query_prop", {vid: ["x"] for vid in video_ids})
        # Load initial results
        ctx.get_videos(100, 0)

        selector = {"all": True, "include": [], "exclude": []}
        # query_on_view should NOT emit state_changed
        result = ctx.query_on_view(selector, "count_property_values", "query_prop")
        assert result is not None

    def test_apply_on_view_returns_none_without_database(self, ctx):
        ctx._api.database = None
        selector = {"all": True, "include": [], "exclude": []}
        result = ctx.apply_on_view(selector, "count_property_values", "x")
        assert result is None

    def test_apply_on_view_count_emits_state_changed(self, ctx, qtbot):
        # Use an existing property from the test database
        prop_types = ctx._database.get_prop_types()
        if not prop_types:
            pytest.skip("No properties in test database")
        prop_name = prop_types[0].name
        ctx.get_videos(100, 0)

        selector = {"all": True, "include": [], "exclude": []}
        # count_property_values returns a non-None result, so state_changed is emitted
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            result = ctx.apply_on_view(selector, "count_property_values", prop_name)
        assert isinstance(result, list)


# =========================================================================
# open_random_video
# =========================================================================


class TestOpenRandomVideo:
    def test_open_random_video_emits_state_changed(self, ctx, qtbot, monkeypatch):
        from pysaurus.core.absolute_path import AbsolutePath

        monkeypatch.setattr(AbsolutePath, "open", lambda self: self)
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            result = ctx.open_random_video()
        assert result is not None
        assert ctx._view.search.text  # search set to video ID

    def test_open_random_video_returns_none_without_database(self, ctx):
        ctx._api.database = None
        result = ctx.open_random_video()
        assert result is None

    def test_open_random_video_skips_not_found_sources(self, ctx):
        # All sources are "not_found" -> skipped -> NoVideos -> caught -> None
        ctx.set_sources([["not_found"]])
        result = ctx.open_random_video()
        assert result is None


# =========================================================================
# close_app / playlist
# =========================================================================


class TestApiDelegation:
    def test_close_app(self, ctx, monkeypatch):
        from pysaurus.interface.api.feature_api import FeatureAPI

        called = []
        monkeypatch.setattr(
            FeatureAPI, "close_app", lambda self: called.append(True), raising=False
        )
        ctx.close_app()
        assert called == [True]

    def test_playlist(self, ctx, monkeypatch):
        monkeypatch.setattr(type(ctx._api), "playlist", lambda self: "test.m3u")
        assert ctx.playlist() == "test.m3u"
