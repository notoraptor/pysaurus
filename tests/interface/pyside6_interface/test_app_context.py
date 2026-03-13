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


# =========================================================================
# Notification processing
# =========================================================================


class TestNotificationProcessing:
    def test_process_database_ready(self, ctx, qtbot):
        from pysaurus.core.notifications import DatabaseReady

        with qtbot.waitSignal(ctx.database_ready, timeout=1000):
            ctx._process_notification(DatabaseReady())

    def test_process_done(self, ctx, qtbot):
        from pysaurus.core.notifications import Done

        with qtbot.waitSignal(ctx.operation_done, timeout=1000):
            ctx._process_notification(Done())

    def test_process_cancelled(self, ctx, qtbot):
        from pysaurus.core.notifications import Cancelled

        with qtbot.waitSignal(ctx.operation_cancelled, timeout=1000):
            ctx._process_notification(Cancelled())

    def test_process_end(self, ctx, qtbot):
        from pysaurus.core.notifications import End

        with qtbot.waitSignal(ctx.operation_ended, timeout=1000):
            ctx._process_notification(End("done"))

    def test_process_profiling_start(self, ctx, qtbot):
        from pysaurus.core.notifications import ProfilingStart

        with qtbot.waitSignal(ctx.profiling_started, timeout=1000):
            ctx._process_notification(ProfilingStart("task"))

    def test_process_profiling_end(self, ctx, qtbot):
        from pysaurus.core.notifications import ProfilingEnd

        with qtbot.waitSignal(ctx.profiling_ended, timeout=1000):
            ctx._process_notification(ProfilingEnd("task", "1.5s"))

    def test_process_job_to_do(self, ctx, qtbot):
        from pysaurus.core.job_notifications import JobToDo

        with qtbot.waitSignal(ctx.job_started, timeout=1000):
            ctx._process_notification(JobToDo("extract", 100, "Extracting"))

    def test_process_job_step(self, ctx, qtbot):
        from pysaurus.core.job_notifications import JobStep

        with qtbot.waitSignal(ctx.job_progress, timeout=1000):
            ctx._process_notification(
                JobStep("extract", "0", 42, 100, title="Extracting")
            )

    def test_process_job_step_none_channel(self, ctx, qtbot):
        from pysaurus.core.job_notifications import JobStep

        with qtbot.waitSignal(ctx.job_progress, timeout=1000):
            ctx._process_notification(
                JobStep("extract", None, 10, 100, title="Extracting")
            )

    def test_generic_signal_always_emitted(self, ctx, qtbot):
        from pysaurus.core.notifications import Done

        with qtbot.waitSignal(ctx.notification_received, timeout=1000):
            ctx._process_notification(Done())


class TestNotificationHandler:
    def test_handler_receives_notification(self, ctx):
        from pysaurus.core.notifications import Done

        received = []

        class Handler:
            def on_notification(self, n):
                received.append(n)

        ctx.set_notification_handler(Handler())
        ctx._process_notification(Done())

        assert len(received) == 1
        assert isinstance(received[0], Done)

    def test_handler_prevents_specific_signals(self, ctx, qtbot):
        from pysaurus.core.notifications import Done

        class Handler:
            def on_notification(self, n):
                pass

        ctx.set_notification_handler(Handler())

        # operation_done should NOT be emitted when handler is set
        emitted = []
        ctx.operation_done.connect(lambda: emitted.append(True))
        ctx._process_notification(Done())

        assert emitted == []

    def test_generic_signal_still_emitted_with_handler(self, ctx, qtbot):
        from pysaurus.core.notifications import Done

        class Handler:
            def on_notification(self, n):
                pass

        ctx.set_notification_handler(Handler())

        with qtbot.waitSignal(ctx.notification_received, timeout=1000):
            ctx._process_notification(Done())

    def test_clear_handler(self, ctx, qtbot):
        from pysaurus.core.notifications import Done

        class Handler:
            def on_notification(self, n):
                pass

        ctx.set_notification_handler(Handler())
        ctx.clear_notification_handler()

        # After clearing, specific signals should be emitted again
        with qtbot.waitSignal(ctx.operation_done, timeout=1000):
            ctx._process_notification(Done())


# =========================================================================
# State facade methods
# =========================================================================


class TestStateFacade:
    def test_has_database(self, ctx):
        assert ctx.has_database()

    def test_has_database_without_db(self, ctx):
        ctx._api.database = None
        assert not ctx.has_database()

    def test_get_database_name(self, ctx):
        name = ctx.get_database_name()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_get_database_name_without_db(self, ctx):
        ctx._api.database = None
        assert ctx.get_database_name() == ""

    def test_get_database_folder_path(self, ctx):
        path = ctx.get_database_folder_path()
        assert isinstance(path, str)
        assert len(path) > 0

    def test_get_database_folder_path_without_db(self, ctx):
        ctx._api.database = None
        assert ctx.get_database_folder_path() == ""


# =========================================================================
# Property type facade methods
# =========================================================================


class TestPropertyTypeFacade:
    def test_get_prop_types(self, ctx):
        types = ctx.get_prop_types()
        assert isinstance(types, list)

    def test_get_prop_types_without_db(self, ctx):
        ctx._api.database = None
        assert ctx.get_prop_types() == []

    def test_create_prop_type_emits_state_changed(self, ctx, qtbot):
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.create_prop_type("new_prop", "str", "", False)
        types = ctx.get_prop_types()
        names = [t.name for t in types]
        assert "new_prop" in names

    def test_rename_prop_type_emits_state_changed(self, ctx, qtbot):
        ctx._database.prop_type_add("rename_me", "str", "", False)
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.rename_prop_type("rename_me", "renamed")
        names = [t.name for t in ctx.get_prop_types()]
        assert "renamed" in names
        assert "rename_me" not in names

    def test_delete_prop_type_emits_state_changed(self, ctx, qtbot):
        ctx._database.prop_type_add("delete_me", "str", "", False)
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.delete_prop_type("delete_me")
        names = [t.name for t in ctx.get_prop_types()]
        assert "delete_me" not in names

    def test_set_prop_type_multiple_emits_state_changed(self, ctx, qtbot):
        ctx._database.prop_type_add("multi_test", "str", "", False)
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.set_prop_type_multiple("multi_test", True)
        types = ctx.get_prop_types(name="multi_test")
        assert types[0].multiple is True


# =========================================================================
# Video entry facade methods
# =========================================================================


class TestVideoEntryFacade:
    def test_get_video_by_id(self, ctx):
        videos = ctx._database.get_videos(include=["video_id"])
        vid = videos[0].video_id
        result = ctx.get_video_by_id(vid)
        assert result is not None
        assert result.video_id == vid

    def test_get_video_by_id_not_found(self, ctx):
        result = ctx.get_video_by_id(-999)
        assert result is None

    def test_get_video_by_id_without_db(self, ctx):
        ctx._api.database = None
        assert ctx.get_video_by_id(1) is None

    def test_delete_video_entry_emits_state_changed(self, ctx, qtbot):
        videos = ctx._database.get_videos(include=["video_id"])
        vid = videos[0].video_id
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.delete_video_entry(vid)
        assert ctx.get_video_by_id(vid) is None

    def test_delete_video_entries_emits_state_changed(self, ctx, qtbot):
        videos = ctx._database.get_videos(include=["video_id"])
        ids = [v.video_id for v in videos[:2]]
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.delete_video_entries(ids)
        for vid in ids:
            assert ctx.get_video_by_id(vid) is None

    def test_delete_video_entry_without_db(self, ctx):
        ctx._api.database = None
        ctx.delete_video_entry(1)  # Should not raise


# =========================================================================
# Property value facade methods
# =========================================================================


class TestPropertyValueFacade:
    def test_get_property_values(self, ctx):
        prop_types = ctx.get_prop_types()
        if not prop_types:
            pytest.skip("No properties")
        result = ctx.get_property_values(prop_types[0].name)
        assert isinstance(result, dict)

    def test_get_property_values_without_db(self, ctx):
        ctx._api.database = None
        assert ctx.get_property_values("x") == {}

    def test_set_video_properties_emits_state_changed(self, ctx, qtbot):
        ctx._database.prop_type_add("test_tag", "str", "", True)
        videos = ctx._database.get_videos(include=["video_id"])
        vid = videos[0].video_id
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.set_video_properties(vid, {"test_tag": ["val1"]})
        values = ctx._database.videos_tag_get("test_tag")
        assert vid in values

    def test_notify_attributes_modified_emits_state_changed(self, ctx, qtbot):
        with qtbot.waitSignal(ctx.state_changed, timeout=1000):
            ctx.notify_attributes_modified(["title"], False)

    def test_notify_attributes_modified_without_db(self, ctx):
        ctx._api.database = None
        # Should not raise or emit
        ctx.notify_attributes_modified(["title"], False)


# =========================================================================
# Database management facade
# =========================================================================


class TestDatabaseManagement:
    def test_get_database_folders(self, ctx):
        folders = ctx.get_database_folders()
        assert isinstance(folders, list)

    def test_get_database_folders_without_db(self, ctx):
        ctx._api.database = None
        assert ctx.get_database_folders() == []

    def test_get_provider_state(self, ctx):
        result = ctx.get_provider_state()
        assert result is not None

    def test_get_provider_state_without_db(self, ctx):
        ctx._api.database = None
        assert ctx.get_provider_state() is None
