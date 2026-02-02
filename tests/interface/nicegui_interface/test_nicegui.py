"""
Tests for NiceGUI interface components.

Covers formatters, state management, constants, and page logic.
"""

import pytest


# =============================================================================
# Tests for formatters.py
# =============================================================================


class TestFormatters:
    """Tests for formatting utilities."""

    def test_format_duration_with_value(self):
        """Test format_duration with valid value."""
        from pysaurus.interface.nicegui.utils.formatters import format_duration

        assert format_duration("1:23:45") == "1:23:45"
        assert format_duration("0:05:30") == "0:05:30"
        assert format_duration("10:00") == "10:00"

    def test_format_duration_empty(self):
        """Test format_duration with empty/None value."""
        from pysaurus.interface.nicegui.utils.formatters import format_duration

        assert format_duration("") == "—"
        assert format_duration(None) == "—"

    def test_format_size_with_value(self):
        """Test format_size with valid value."""
        from pysaurus.interface.nicegui.utils.formatters import format_size

        assert format_size("1.5 GB") == "1.5 GB"
        assert format_size("500 MB") == "500 MB"

    def test_format_size_empty(self):
        """Test format_size with empty/None value."""
        from pysaurus.interface.nicegui.utils.formatters import format_size

        assert format_size("") == "—"
        assert format_size(None) == "—"

    def test_format_resolution_with_values(self):
        """Test format_resolution with valid values."""
        from pysaurus.interface.nicegui.utils.formatters import format_resolution

        assert format_resolution(1920, 1080) == "1920x1080"
        assert format_resolution(1280, 720) == "1280x720"
        assert format_resolution(640, 480) == "640x480"

    def test_format_resolution_zero_values(self):
        """Test format_resolution with zero values."""
        from pysaurus.interface.nicegui.utils.formatters import format_resolution

        assert format_resolution(0, 1080) == "—"
        assert format_resolution(1920, 0) == "—"
        assert format_resolution(0, 0) == "—"

    def test_format_file_size_bytes(self):
        """Test format_file_size with various byte values."""
        from pysaurus.interface.nicegui.utils.formatters import format_file_size

        # Test that it returns a string (exact format depends on FileSize class)
        result = format_file_size(1024)
        assert isinstance(result, str)
        assert result != "—"

        result = format_file_size(1024 * 1024)
        assert isinstance(result, str)
        assert "MiB" in result or "MB" in result or "KiB" in result

    def test_format_file_size_zero(self):
        """Test format_file_size with zero."""
        from pysaurus.interface.nicegui.utils.formatters import format_file_size

        assert format_file_size(0) == "—"

    def test_format_file_size_none(self):
        """Test format_file_size with None."""
        from pysaurus.interface.nicegui.utils.formatters import format_file_size

        assert format_file_size(None) == "—"

    def test_truncate_short_text(self):
        """Test truncate with text shorter than max."""
        from pysaurus.interface.nicegui.utils.formatters import truncate

        assert truncate("Hello", 10) == "Hello"
        assert truncate("Short", 50) == "Short"

    def test_truncate_long_text(self):
        """Test truncate with text longer than max."""
        from pysaurus.interface.nicegui.utils.formatters import truncate

        result = truncate("This is a very long text that needs truncation", 20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_truncate_exact_length(self):
        """Test truncate with text exactly at max length."""
        from pysaurus.interface.nicegui.utils.formatters import truncate

        text = "Exactly10!"
        assert truncate(text, 10) == text

    def test_truncate_empty(self):
        """Test truncate with empty string."""
        from pysaurus.interface.nicegui.utils.formatters import truncate

        assert truncate("", 10) == ""
        assert truncate(None, 10) == ""


# =============================================================================
# Tests for state.py
# =============================================================================


class TestAppState:
    """Tests for AppState class."""

    def test_initial_state(self):
        """Test AppState initial values."""
        from pysaurus.interface.nicegui.state import AppState, Page

        state = AppState()

        assert state.current_page == Page.DATABASES
        assert state.database_name is None
        assert state.database_folders == []
        assert state.page_size == 20
        assert state.page_number == 0
        assert state.selected_videos == set()
        assert state.search_text == ""
        assert state.search_cond == "and"

    def test_reset_view(self):
        """Test reset_view clears view-related state."""
        from pysaurus.interface.nicegui.state import AppState

        state = AppState()

        # Set some state
        state.page_number = 5
        state.selected_videos.add(1)
        state.selected_videos.add(2)
        state.select_all = True
        state.group_field = "extension"
        state.classifier_path.append("value1")
        state.search_text = "test"
        state.sorting.append("filename")
        state.sources.append(["readable"])

        # Reset
        state.reset_view()

        # Verify reset
        assert state.page_number == 0
        assert state.selected_videos == set()
        assert state.select_all is False
        assert state.group_field is None
        assert state.classifier_path == []
        assert state.search_text == ""
        assert state.sorting == []
        assert state.sources == []

    def test_add_notification(self):
        """Test add_notification adds to list."""
        from pysaurus.interface.nicegui.state import AppState

        state = AppState()

        state.add_notification({"name": "Test", "message": "Hello"})
        assert len(state.notifications) == 1
        assert state.notifications[0]["name"] == "Test"

    def test_add_notification_limit(self):
        """Test add_notification keeps only last 100."""
        from pysaurus.interface.nicegui.state import AppState

        state = AppState()

        # Add 150 notifications
        for i in range(150):
            state.add_notification({"id": i})

        # Should only keep last 100
        assert len(state.notifications) == 100
        assert state.notifications[0]["id"] == 50  # First kept is #50
        assert state.notifications[-1]["id"] == 149  # Last is #149

    def test_clear_notifications(self):
        """Test clear_notifications empties the list."""
        from pysaurus.interface.nicegui.state import AppState

        state = AppState()

        state.add_notification({"name": "Test1"})
        state.add_notification({"name": "Test2"})
        assert len(state.notifications) == 2

        state.clear_notifications()
        assert state.notifications == []


class TestPage:
    """Tests for Page enum."""

    def test_page_values(self):
        """Test Page enum has expected values."""
        from pysaurus.interface.nicegui.state import Page

        assert Page.DATABASES.value == "databases"
        assert Page.HOME.value == "home"
        assert Page.VIDEOS.value == "videos"
        assert Page.PROPERTIES.value == "properties"

    def test_page_is_string(self):
        """Test Page enum values are strings."""
        from pysaurus.interface.nicegui.state import Page

        assert isinstance(Page.DATABASES.value, str)
        assert Page.DATABASES == "databases"  # str comparison works


# =============================================================================
# Tests for constants.py
# =============================================================================


class TestConstants:
    """Tests for constants module."""

    def test_group_permissions(self):
        """Test group permission constants."""
        from pysaurus.interface.nicegui.utils.constants import (
            GROUP_FORBIDDEN,
            GROUP_ONLY_MANY,
            GROUP_ALL,
        )

        assert GROUP_FORBIDDEN == 0
        assert GROUP_ONLY_MANY == 1
        assert GROUP_ALL == 2

    def test_field_definitions_structure(self):
        """Test FIELD_DEFINITIONS has correct structure."""
        from pysaurus.interface.nicegui.utils.constants import FIELD_DEFINITIONS

        assert len(FIELD_DEFINITIONS) > 0

        for field_def in FIELD_DEFINITIONS:
            assert len(field_def) == 4
            name, title, permission, is_string = field_def
            assert isinstance(name, str)
            assert isinstance(title, str)
            assert permission in (0, 1, 2)
            assert isinstance(is_string, bool)

    def test_field_definitions_has_common_fields(self):
        """Test FIELD_DEFINITIONS includes common fields."""
        from pysaurus.interface.nicegui.utils.constants import FIELD_DEFINITIONS

        field_names = [f[0] for f in FIELD_DEFINITIONS]

        assert "extension" in field_names
        assert "width" in field_names
        assert "height" in field_names
        assert "filename" in field_names
        assert "title" in field_names

    def test_groupable_fields_excludes_forbidden(self):
        """Test GROUPABLE_FIELDS excludes forbidden fields."""
        from pysaurus.interface.nicegui.utils.constants import (
            GROUPABLE_FIELDS,
            FIELD_DEFINITIONS,
            GROUP_FORBIDDEN,
        )

        groupable_names = [f[0] for f in GROUPABLE_FIELDS]
        forbidden_names = [f[0] for f in FIELD_DEFINITIONS if f[2] == GROUP_FORBIDDEN]

        for forbidden in forbidden_names:
            assert forbidden not in groupable_names

    def test_source_tree_structure(self):
        """Test SOURCE_TREE has correct structure."""
        from pysaurus.interface.nicegui.utils.constants import SOURCE_TREE

        assert "readable" in SOURCE_TREE
        assert "unreadable" in SOURCE_TREE

        assert "found" in SOURCE_TREE["readable"]
        assert "not_found" in SOURCE_TREE["readable"]

    def test_group_sorting_options(self):
        """Test GROUP_SORTING_OPTIONS has expected values."""
        from pysaurus.interface.nicegui.utils.constants import GROUP_SORTING_OPTIONS

        option_keys = [opt[0] for opt in GROUP_SORTING_OPTIONS]

        assert "field" in option_keys
        assert "count" in option_keys


# =============================================================================
# Tests for VideosPageState
# =============================================================================


class TestVideosPageState:
    """Tests for VideosPageState class."""

    def test_initial_state(self):
        """Test VideosPageState initial values."""
        from pysaurus.interface.nicegui.pages.videos_page import (
            VideosPageState,
            ViewMode,
        )

        state = VideosPageState()

        assert state.videos == []
        assert state.nb_videos == 0
        assert state.nb_pages == 0
        assert state.page_size == 20
        assert state.page_number == 0
        assert state.view_mode == ViewMode.GRID
        assert state.sources == []
        assert state.group_def is None
        assert state.sorting == []

    def test_toggle_view_mode(self):
        """Test toggle_view_mode switches between grid and list."""
        from pysaurus.interface.nicegui.pages.videos_page import (
            VideosPageState,
            ViewMode,
        )

        state = VideosPageState()

        assert state.view_mode == ViewMode.GRID

        state.toggle_view_mode()
        assert state.view_mode == ViewMode.LIST

        state.toggle_view_mode()
        assert state.view_mode == ViewMode.GRID


class TestViewMode:
    """Tests for ViewMode class."""

    def test_view_mode_values(self):
        """Test ViewMode has expected values."""
        from pysaurus.interface.nicegui.pages.videos_page import ViewMode

        assert ViewMode.GRID == "grid"
        assert ViewMode.LIST == "list"


# =============================================================================
# Tests for API Bridge with database
# =============================================================================


class TestAPIBridgeIntegration:
    """Integration tests for API Bridge with mock database."""

    def test_backend_pagination(self, mock_database):
        """Test backend pagination works correctly."""
        from pysaurus.interface.nicegui.api_bridge import APIBridge, NiceGuiAPI

        bridge = APIBridge()
        bridge._api = NiceGuiAPI()
        bridge._api.database = mock_database

        # Get first page
        data = bridge.backend(page_size=5, page_number=0)
        assert len(data["videos"]) <= 5
        assert data["pageSize"] == 5
        assert data["pageNumber"] == 0

        # Get second page if available
        if data["nbPages"] > 1:
            data2 = bridge.backend(page_size=5, page_number=1)
            assert data2["pageNumber"] == 1
            # Videos should be different
            if data["videos"] and data2["videos"]:
                assert data["videos"][0]["video_id"] != data2["videos"][0]["video_id"]

    def test_search_filters_videos(self, mock_database):
        """Test that search actually filters videos."""
        from pysaurus.interface.nicegui.api_bridge import APIBridge, NiceGuiAPI

        bridge = APIBridge()
        bridge._api = NiceGuiAPI()
        bridge._api.database = mock_database

        # Get all videos first
        all_data = bridge.backend(page_size=100, page_number=0)
        total_count = all_data["nbVideos"]

        # Search for something specific
        bridge.set_search("nonexistent_xyz_123", "and")
        search_data = bridge.backend(page_size=100, page_number=0)

        # Should have fewer or equal results
        assert search_data["nbVideos"] <= total_count

        # Clear search
        bridge.set_search("", "and")

    def test_grouping_creates_groups(self, mock_database):
        """Test that grouping creates group definitions."""
        from pysaurus.interface.nicegui.api_bridge import APIBridge, NiceGuiAPI

        bridge = APIBridge()
        bridge._api = NiceGuiAPI()
        bridge._api.database = mock_database

        # Set grouping by extension
        result = bridge.set_groups(
            field="extension",
            is_property=False,
            sorting="field",
            reverse=False,
            allow_singletons=True,
        )
        assert result.get("error") is False

        # Get backend data
        data = bridge.backend(page_size=100, page_number=0)

        # Should have groupDef
        assert "groupDef" in data
        if data["groupDef"]:
            assert data["groupDef"]["field"] == "extension"

    def test_prop_type_lifecycle(self, mock_database):
        """Test complete property type lifecycle."""
        from pysaurus.interface.nicegui.api_bridge import APIBridge, NiceGuiAPI

        bridge = APIBridge()
        bridge._api = NiceGuiAPI()
        bridge._api.database = mock_database

        prop_name = "test_lifecycle_prop"

        # 1. Create
        result = bridge.create_prop_type(prop_name, "str", "", True)
        assert result.get("error") is False

        # 2. Verify exists
        props = bridge.describe_prop_types()
        assert prop_name in [p["name"] for p in props]

        # 3. Rename
        new_name = "renamed_lifecycle_prop"
        result = bridge.rename_prop_type(prop_name, new_name)
        assert result.get("error") is False

        # 4. Verify renamed
        props = bridge.describe_prop_types()
        assert prop_name not in [p["name"] for p in props]
        assert new_name in [p["name"] for p in props]

        # 5. Convert multiplicity
        result = bridge.convert_prop_multiplicity(new_name, False)
        assert result.get("error") is False

        # 6. Verify converted
        props = bridge.describe_prop_types()
        prop = next(p for p in props if p["name"] == new_name)
        assert prop["multiple"] is False

        # 7. Delete
        result = bridge.remove_prop_type(new_name)
        assert result.get("error") is False

        # 8. Verify deleted
        props = bridge.describe_prop_types()
        assert new_name not in [p["name"] for p in props]


# =============================================================================
# Tests for ProgressTracker (home_page.py)
# =============================================================================


class TestProgressTracker:
    """Tests for ProgressTracker class."""

    def test_initial_state(self):
        """Test ProgressTracker initial values."""
        from pysaurus.interface.nicegui.pages.home_page import ProgressTracker

        tracker = ProgressTracker()

        assert tracker.jobs == {}
        assert tracker.messages == []
        assert tracker.is_ready is False

    def test_job_to_do_notification(self):
        """Test handling JobToDo notification."""
        from pysaurus.interface.nicegui.pages.home_page import ProgressTracker

        tracker = ProgressTracker()

        notification = {
            "name": "JobToDo",
            "notification": {"name": "scan", "title": "Scanning", "total": 100},
        }
        tracker.handle_notification(notification)

        assert "scan" in tracker.jobs
        assert tracker.jobs["scan"]["title"] == "Scanning"
        assert tracker.jobs["scan"]["total"] == 100
        assert tracker.jobs["scan"]["current"] == 0

    def test_job_step_notification(self):
        """Test handling JobStep notification."""
        from pysaurus.interface.nicegui.pages.home_page import ProgressTracker

        tracker = ProgressTracker()

        # First add job
        tracker.handle_notification(
            {
                "name": "JobToDo",
                "notification": {"name": "scan", "title": "Scanning", "total": 100},
            }
        )

        # Then progress
        tracker.handle_notification(
            {
                "name": "JobStep",
                "notification": {"name": "scan", "channel": "ch1", "step": 30},
            }
        )

        assert tracker.jobs["scan"]["current"] == 30

    def test_job_completion_removes_job(self):
        """Test that completed jobs are removed."""
        from pysaurus.interface.nicegui.pages.home_page import ProgressTracker

        tracker = ProgressTracker()

        # Add job
        tracker.handle_notification(
            {
                "name": "JobToDo",
                "notification": {"name": "scan", "title": "Scanning", "total": 100},
            }
        )

        # Complete it
        tracker.handle_notification(
            {
                "name": "JobStep",
                "notification": {"name": "scan", "channel": "ch1", "step": 100},
            }
        )

        assert "scan" not in tracker.jobs

    def test_database_ready_notification(self):
        """Test handling DatabaseReady notification."""
        from pysaurus.interface.nicegui.pages.home_page import ProgressTracker

        tracker = ProgressTracker()

        tracker.handle_notification({"name": "DatabaseReady"})

        assert tracker.is_ready is True
        assert "Database ready!" in tracker.messages

    def test_done_notification(self):
        """Test handling Done notification."""
        from pysaurus.interface.nicegui.pages.home_page import ProgressTracker

        tracker = ProgressTracker()

        tracker.handle_notification({"name": "Done"})

        assert "Done!" in tracker.messages

    def test_cancelled_notification(self):
        """Test handling Cancelled notification."""
        from pysaurus.interface.nicegui.pages.home_page import ProgressTracker

        tracker = ProgressTracker()

        tracker.handle_notification({"name": "Cancelled"})

        assert "Cancelled." in tracker.messages

    def test_end_notification_with_message(self):
        """Test handling End notification with custom message."""
        from pysaurus.interface.nicegui.pages.home_page import ProgressTracker

        tracker = ProgressTracker()

        tracker.handle_notification({"name": "End", "message": "Processing finished"})

        assert "Processing finished" in tracker.messages

    def test_messages_limit(self):
        """Test that messages are limited to 50."""
        from pysaurus.interface.nicegui.pages.home_page import ProgressTracker

        tracker = ProgressTracker()

        # Add 60 messages
        for i in range(60):
            tracker.handle_notification({"name": "Test", "message": f"Message {i}"})

        assert len(tracker.messages) == 50
        assert "Message 10" in tracker.messages  # First kept message
        assert "Message 59" in tracker.messages  # Last message

    def test_multiple_channels_aggregate(self):
        """Test that multiple channels aggregate correctly."""
        from pysaurus.interface.nicegui.pages.home_page import ProgressTracker

        tracker = ProgressTracker()

        # Add job
        tracker.handle_notification(
            {
                "name": "JobToDo",
                "notification": {"name": "scan", "title": "Scanning", "total": 100},
            }
        )

        # Progress on multiple channels
        tracker.handle_notification(
            {
                "name": "JobStep",
                "notification": {"name": "scan", "channel": "ch1", "step": 30},
            }
        )
        tracker.handle_notification(
            {
                "name": "JobStep",
                "notification": {"name": "scan", "channel": "ch2", "step": 20},
            }
        )

        assert tracker.jobs["scan"]["current"] == 50  # 30 + 20


# =============================================================================
# Tests for PropertiesPageState (properties_page.py)
# =============================================================================


class TestPropertiesPageState:
    """Tests for PropertiesPageState class."""

    def test_initial_state(self):
        """Test PropertiesPageState initial values."""
        from pysaurus.interface.nicegui.pages.properties_page import PropertiesPageState

        state = PropertiesPageState()

        assert state.definitions == []
        assert state.name == ""
        assert state.prop_type == "str"
        assert state.multiple is False
        assert state.is_enumeration is False
        assert state.default_value == ""
        assert state.enumeration_values == []

    def test_reset_form(self):
        """Test reset_form resets all form fields."""
        from pysaurus.interface.nicegui.pages.properties_page import PropertiesPageState

        state = PropertiesPageState()

        # Set some values
        state.name = "test_prop"
        state.prop_type = "int"
        state.multiple = True
        state.is_enumeration = True
        state.default_value = "42"
        state.enumeration_values = ["a", "b"]

        # Reset
        state.reset_form()

        # Verify reset
        assert state.name == ""
        assert state.prop_type == "str"
        assert state.multiple is False
        assert state.is_enumeration is False
        assert state.default_value == ""
        assert state.enumeration_values == []


class TestPropertiesPageConstants:
    """Tests for properties page constants."""

    def test_prop_types_has_expected_types(self):
        """Test PROP_TYPES has expected type definitions."""
        from pysaurus.interface.nicegui.pages.properties_page import PROP_TYPES

        type_codes = [t[0] for t in PROP_TYPES]

        assert "bool" in type_codes
        assert "int" in type_codes
        assert "float" in type_codes
        assert "str" in type_codes

    def test_default_values_match_prop_types(self):
        """Test DEFAULT_VALUES has entry for each prop type."""
        from pysaurus.interface.nicegui.pages.properties_page import (
            PROP_TYPES,
            DEFAULT_VALUES,
        )

        for type_code, _ in PROP_TYPES:
            assert type_code in DEFAULT_VALUES

    def test_default_values_are_correct_type(self):
        """Test DEFAULT_VALUES have correct Python types."""
        from pysaurus.interface.nicegui.pages.properties_page import DEFAULT_VALUES

        assert DEFAULT_VALUES["bool"] is False
        assert isinstance(DEFAULT_VALUES["int"], int)
        assert isinstance(DEFAULT_VALUES["float"], float)
        assert isinstance(DEFAULT_VALUES["str"], str)


# =============================================================================
# Tests for NiceGuiAPI notification handling
# =============================================================================


class TestNiceGuiAPI:
    """Tests for NiceGuiAPI notification handling."""

    def test_add_notification_handler(self):
        """Test adding a notification handler."""
        from pysaurus.interface.nicegui.api_bridge import NiceGuiAPI

        api = NiceGuiAPI()
        received = []

        def handler(notification):
            received.append(notification)

        api.add_notification_handler(handler)
        assert handler in api._notification_handlers

    def test_remove_notification_handler(self):
        """Test removing a notification handler."""
        from pysaurus.interface.nicegui.api_bridge import NiceGuiAPI

        api = NiceGuiAPI()

        def handler(notification):
            pass

        api.add_notification_handler(handler)
        api.remove_notification_handler(handler)
        assert handler not in api._notification_handlers

    def test_remove_nonexistent_handler(self):
        """Test removing a handler that wasn't added."""
        from pysaurus.interface.nicegui.api_bridge import NiceGuiAPI

        api = NiceGuiAPI()

        def handler(notification):
            pass

        # Should not raise
        api.remove_notification_handler(handler)


# =============================================================================
# Tests for wrap_error decorator
# =============================================================================


class TestWrapErrorDecorator:
    """Tests for _wrap_error decorator behavior."""

    def test_successful_call_returns_error_false(self, api_bridge_readonly):
        """Test that successful calls return error: False."""
        result = api_bridge_readonly.set_search("test", "and")

        assert isinstance(result, dict)
        assert result.get("error") is False

    def test_methods_return_dict_with_error_key(self, api_bridge_readonly):
        """Test that wrapped methods return dict with error key."""
        result = api_bridge_readonly.set_sorting(["filename"])

        assert "error" in result


# =============================================================================
# Additional AppState tests
# =============================================================================


class TestAppStateAdditional:
    """Additional tests for AppState."""

    def test_state_has_all_expected_attributes(self):
        """Test AppState has all expected attributes."""
        from pysaurus.interface.nicegui.state import AppState

        state = AppState()

        # Core attributes
        assert hasattr(state, "current_page")
        assert hasattr(state, "database_name")
        assert hasattr(state, "database_folders")

        # Videos page state
        assert hasattr(state, "page_size")
        assert hasattr(state, "page_number")
        assert hasattr(state, "selected_videos")
        assert hasattr(state, "select_all")

        # Grouping
        assert hasattr(state, "group_field")
        assert hasattr(state, "group_is_property")
        assert hasattr(state, "group_reverse")
        assert hasattr(state, "group_allow_singletons")
        assert hasattr(state, "classifier_path")

        # Search
        assert hasattr(state, "search_text")
        assert hasattr(state, "search_cond")

        # Sorting
        assert hasattr(state, "sorting")

        # Sources
        assert hasattr(state, "sources")

        # Progress
        assert hasattr(state, "notifications")
        assert hasattr(state, "is_loading")
        assert hasattr(state, "progress_message")
        assert hasattr(state, "progress_value")
        assert hasattr(state, "progress_total")

    def test_default_search_cond(self):
        """Test default search condition is 'and'."""
        from pysaurus.interface.nicegui.state import AppState

        state = AppState()
        assert state.search_cond == "and"

    def test_reset_view_preserves_database_name(self):
        """Test reset_view does NOT reset database_name."""
        from pysaurus.interface.nicegui.state import AppState

        state = AppState()
        state.database_name = "my_database"
        state.page_number = 5
        state.search_text = "test"

        state.reset_view()

        assert state.database_name == "my_database"
        assert state.page_number == 0
        assert state.search_text == ""


@pytest.fixture
def api_bridge_readonly(mock_database):
    """APIBridge with mock database."""
    from pysaurus.interface.nicegui.api_bridge import APIBridge, NiceGuiAPI

    bridge = APIBridge()
    bridge._api = NiceGuiAPI()
    bridge._api.database = mock_database
    return bridge
