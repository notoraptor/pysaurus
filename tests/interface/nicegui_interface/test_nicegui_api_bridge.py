"""
Tests for NiceGUI API Bridge.

Tests that direct Python calls work correctly instead of string-based __run_feature__.
Uses mock_database for fast in-memory testing.
"""

import pytest

from pysaurus.interface.nicegui.api_bridge import APIBridge, NiceGuiAPI


@pytest.fixture
def api_bridge_readonly(mock_database):
    """APIBridge with mock database (read-only semantics)."""
    bridge = APIBridge()
    bridge._api = NiceGuiAPI()
    bridge._api.database = mock_database
    return bridge


@pytest.fixture
def api_bridge_writable(mock_database):
    """APIBridge with mock database (write semantics)."""
    bridge = APIBridge()
    bridge._api = NiceGuiAPI()
    bridge._api.database = mock_database
    return bridge


class TestAPIBridgeReadOnly:
    """Tests that don't modify the database."""

    def test_get_constants(self, api_bridge_readonly):
        """Test getting constants."""
        constants = api_bridge_readonly.get_constants()
        assert isinstance(constants, dict)
        assert "PYTHON_APP_NAME" in constants

    def test_describe_prop_types(self, api_bridge_readonly):
        """Test getting property types."""
        prop_types = api_bridge_readonly.describe_prop_types()
        assert isinstance(prop_types, list)
        # Mock has 2 property types: genre and rating
        assert len(prop_types) == 2

    def test_backend_returns_dict(self, api_bridge_readonly):
        """Test backend() returns dict with expected keys."""
        data = api_bridge_readonly.backend(page_size=10, page_number=0)

        assert isinstance(data, dict)
        assert "videos" in data
        assert "pageSize" in data
        assert "pageNumber" in data
        assert "nbPages" in data
        assert "nbVideos" in data
        assert data["pageSize"] == 10
        assert data["pageNumber"] == 0

    def test_get_python_backend_returns_context(self, api_bridge_readonly):
        """Test get_python_backend() returns DatabaseContext object."""
        from pysaurus.video.database_context import DatabaseContext

        context = api_bridge_readonly.get_python_backend(page_size=10, page_number=0)

        assert isinstance(context, DatabaseContext)
        assert context.name == "test_database"
        assert isinstance(context.folders, list)

    def test_backend_videos_have_expected_fields(self, api_bridge_readonly):
        """Test that videos have expected fields."""
        data = api_bridge_readonly.backend(page_size=10, page_number=0)

        assert len(data["videos"]) > 0
        video = data["videos"][0]
        # Check essential fields
        assert "video_id" in video
        assert "title" in video
        assert "filename" in video

    def test_backend_returns_correct_video_count(self, api_bridge_readonly):
        """Test that backend returns correct number of videos."""
        data = api_bridge_readonly.backend(page_size=10, page_number=0)

        # Mock has 5 videos
        assert data["nbVideos"] == 5
        assert len(data["videos"]) == 5


class TestAPIBridgeViewOperations:
    """Tests for view/provider operations (read-only)."""

    def test_set_search(self, api_bridge_readonly):
        """Test setting search filter."""
        result = api_bridge_readonly.set_search("test", "and")
        assert result.get("error") is False

    def test_set_search_filters_videos(self, api_bridge_readonly):
        """Test that search actually filters videos."""
        bridge = api_bridge_readonly

        # Get all videos
        all_data = bridge.backend(page_size=100, page_number=0)
        total = all_data["nbVideos"]

        # Search for something that won't match
        bridge.set_search("nonexistent_xyz_123", "and")
        search_data = bridge.backend(page_size=100, page_number=0)
        assert search_data["nbVideos"] < total

        # Search for something that matches
        bridge.set_search("Video", "and")
        search_data = bridge.backend(page_size=100, page_number=0)
        assert search_data["nbVideos"] > 0

    def test_set_sources(self, api_bridge_readonly):
        """Test setting sources filter."""
        result = api_bridge_readonly.set_sources([["readable"]])
        assert result.get("error") is False

    def test_set_sources_filters_videos(self, api_bridge_readonly):
        """Test that sources filter works."""
        bridge = api_bridge_readonly

        # Filter to only readable videos
        bridge.set_sources([["readable"]])
        data = bridge.backend(page_size=100, page_number=0)

        # All videos should be readable
        for video in data["videos"]:
            assert video["readable"] is True

    def test_set_groups(self, api_bridge_readonly):
        """Test setting grouping."""
        result = api_bridge_readonly.set_groups(
            field="extension",
            is_property=False,
            sorting="field",
            reverse=False,
            allow_singletons=True,
        )
        assert result.get("error") is False

    def test_set_sorting(self, api_bridge_readonly):
        """Test setting sorting."""
        result = api_bridge_readonly.set_sorting(["filename"])
        assert result.get("error") is False

    def test_set_sorting_descending(self, api_bridge_readonly):
        """Test setting descending sorting."""
        result = api_bridge_readonly.set_sorting(["-filename"])
        assert result.get("error") is False


class TestAPIBridgeWriteOperations:
    """Tests that modify the database (use mock_database)."""

    def test_create_and_remove_prop_type(self, api_bridge_writable):
        """Test creating and removing a property type."""
        bridge = api_bridge_writable

        # Create property
        result = bridge.create_prop_type("test_prop", "str", "", True)
        assert result.get("error") is False

        # Verify it exists
        props = bridge.describe_prop_types()
        prop_names = [p["name"] for p in props]
        assert "test_prop" in prop_names

        # Remove property
        result = bridge.remove_prop_type("test_prop")
        assert result.get("error") is False

        # Verify it's gone
        props = bridge.describe_prop_types()
        prop_names = [p["name"] for p in props]
        assert "test_prop" not in prop_names

    def test_rename_prop_type(self, api_bridge_writable):
        """Test renaming a property type."""
        bridge = api_bridge_writable

        # Create property
        bridge.create_prop_type("old_prop_name", "str", "", True)

        # Rename it
        result = bridge.rename_prop_type("old_prop_name", "new_prop_name")
        assert result.get("error") is False

        # Verify rename
        props = bridge.describe_prop_types()
        prop_names = [p["name"] for p in props]
        assert "old_prop_name" not in prop_names
        assert "new_prop_name" in prop_names

        # Cleanup
        bridge.remove_prop_type("new_prop_name")

    def test_convert_prop_multiplicity(self, api_bridge_writable):
        """Test converting property multiplicity."""
        bridge = api_bridge_writable

        # Create single-value property
        bridge.create_prop_type("single_prop", "str", "", False)

        # Convert to multiple
        result = bridge.convert_prop_multiplicity("single_prop", True)
        assert result.get("error") is False

        # Verify
        props = bridge.describe_prop_types()
        single_prop = next(p for p in props if p["name"] == "single_prop")
        assert single_prop["multiple"] is True

        # Cleanup
        bridge.remove_prop_type("single_prop")

    def test_mark_as_read(self, api_bridge_writable):
        """Test toggling watched status."""
        bridge = api_bridge_writable
        db = bridge.api.database

        # Get a video
        video = db.get_videos()[0]
        video_id = video.video_id
        initial_watched = video.watched

        # Toggle watched status
        result = bridge.mark_as_read(video_id)
        assert result.get("error") is False

        # Verify it toggled
        video_after = db.get_videos(where={"video_id": video_id})[0]
        assert video_after.watched != initial_watched

        # Toggle back
        bridge.mark_as_read(video_id)
        video_final = db.get_videos(where={"video_id": video_id})[0]
        assert video_final.watched == initial_watched

    def test_set_video_properties(self, api_bridge_writable):
        """Test setting properties for a video."""
        bridge = api_bridge_writable
        db = bridge.api.database

        # Create property
        bridge.create_prop_type("test_tags", "str", "", True)

        # Get a video
        video = db.get_videos()[0]
        video_id = video.video_id

        # Set properties
        result = bridge.set_video_properties(video_id, {"test_tags": ["tag1", "tag2"]})
        assert result.get("error") is False

        # Verify
        tags = db.videos_tag_get("test_tags", indices=[video_id])
        assert video_id in tags
        assert set(tags[video_id]) == {"tag1", "tag2"}

        # Cleanup
        bridge.remove_prop_type("test_tags")


class TestAPIBridgeErrorHandling:
    """Tests for error handling."""

    def test_error_wrapped_correctly(self, api_bridge_writable):
        """Test that errors are wrapped in error dict."""
        bridge = api_bridge_writable

        # Try to remove non-existent property
        result = bridge.remove_prop_type("nonexistent_property_12345")

        # Should return error dict, not raise exception
        assert isinstance(result, dict)
        assert result.get("error") is True

    def test_backend_with_invalid_page(self, api_bridge_readonly):
        """Test backend with edge case page numbers."""
        bridge = api_bridge_readonly

        # Very large page number should return empty videos
        data = bridge.backend(page_size=10, page_number=99999)
        assert isinstance(data, dict)
        assert "videos" in data
        assert len(data["videos"]) == 0

    def test_create_duplicate_prop_type_fails(self, api_bridge_writable):
        """Test that creating duplicate property type fails."""
        bridge = api_bridge_writable

        # Create property
        bridge.create_prop_type("dup_prop", "str", "", True)

        # Try to create again - should fail
        result = bridge.create_prop_type("dup_prop", "str", "", True)
        assert result.get("error") is True

        # Cleanup
        bridge.remove_prop_type("dup_prop")


class TestAPIBridgePagination:
    """Tests for pagination functionality."""

    def test_pagination_page_size(self, api_bridge_readonly):
        """Test that page size is respected."""
        bridge = api_bridge_readonly

        data = bridge.backend(page_size=2, page_number=0)
        assert len(data["videos"]) == 2
        assert data["pageSize"] == 2

    def test_pagination_multiple_pages(self, api_bridge_readonly):
        """Test multiple pages."""
        bridge = api_bridge_readonly

        # Page 0
        page0 = bridge.backend(page_size=2, page_number=0)
        # Page 1
        page1 = bridge.backend(page_size=2, page_number=1)

        # Should have different videos
        ids0 = {v["video_id"] for v in page0["videos"]}
        ids1 = {v["video_id"] for v in page1["videos"]}
        assert ids0.isdisjoint(ids1)

    def test_pagination_nb_pages_calculated(self, api_bridge_readonly):
        """Test that nbPages is calculated correctly."""
        bridge = api_bridge_readonly

        # 5 videos with page_size=2 should be 3 pages
        data = bridge.backend(page_size=2, page_number=0)
        assert data["nbPages"] == 3


class TestAPIBridgeVideoFields:
    """Tests for video field values."""

    def test_video_has_all_expected_fields(self, api_bridge_readonly):
        """Test that video dict has all expected fields."""
        data = api_bridge_readonly.backend(page_size=10, page_number=0)
        video = data["videos"][0]

        expected_fields = [
            "video_id",
            "title",
            "filename",
            "extension",
            "width",
            "height",
            "file_size",
            "readable",
            "found",
            "watched",
            "properties",
        ]
        for field in expected_fields:
            assert field in video, f"Missing field: {field}"

    def test_video_properties_accessible(self, api_bridge_readonly):
        """Test that video properties are accessible."""
        data = api_bridge_readonly.backend(page_size=10, page_number=0)

        # Find a video with properties
        for video in data["videos"]:
            if video["properties"]:
                assert isinstance(video["properties"], dict)
                break
