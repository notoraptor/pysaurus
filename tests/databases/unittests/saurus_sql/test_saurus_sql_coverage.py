"""
Additional tests to improve coverage of saurus.sql module.

These tests target specific code paths not covered by test_saurus_sql.py,
focusing on edge cases and optimization flags in video_mega_search().
"""

import pytest

from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.dbview.view_context import ViewContext


@pytest.fixture
def disk_database(example_saurus_database) -> AbstractDatabase:
    """Read-only Saurus SQL database."""
    return example_saurus_database


@pytest.fixture
def memory_database(example_saurus_database_memory) -> AbstractDatabase:
    """In-memory Saurus SQL database for write tests."""
    return example_saurus_database_memory


class TestVideoMegaSearchOptimizations:
    """Tests for video_mega_search optimization flags."""

    def test_count_videos_basic(self, disk_database):
        """Test count_videos method."""
        # Count all found videos
        count = disk_database.ops.count_videos("found")
        assert count == 90

        # Count unreadable videos
        count_unreadable = disk_database.ops.count_videos("unreadable")
        assert count_unreadable == 3

        # Count not_found videos
        count_not_found = disk_database.ops.count_videos("not_found")
        assert count_not_found == 3

    def test_has_video_method(self, disk_database):
        """Test has_video method (exists check)."""
        # Check if a specific video exists by video_id
        exists = disk_database.ops.has_video(video_id=196)
        assert exists is True

        # Check if a video with impossible ID exists
        exists_impossible = disk_database.ops.has_video(video_id=999999)
        assert exists_impossible is False

    def test_get_videos_by_ids(self, disk_database):
        """Test getting videos by their IDs."""
        # Get all videos (including discarded)
        all_videos = disk_database.get_videos(include=())
        all_ids = [v.video_id for v in all_videos]
        # Total: 99 entries (6 discarded + 3 unreadable + 3 not_found + 87 valid)
        assert len(all_ids) == 99
        assert all(isinstance(vid, int) for vid in all_ids)

        # Get filtered video IDs (matches pattern from test_saurus_sql.py)
        specific_ids = [196, 114]
        videos = disk_database.get_videos(include=(), where={"video_id": specific_ids})
        fetched_ids = [v.video_id for v in videos]
        # Should get exactly the requested videos
        assert len(fetched_ids) == len(specific_ids)
        assert set(fetched_ids) == set(specific_ids)

    def test_get_videos_with_include_filter(self, disk_database):
        """Test include parameter to fetch only specific fields."""
        # Fetch videos with minimal fields (no extra queries)
        # include=() means no extra properties/languages/errors
        videos = disk_database.get_videos(include=(), where={"video_id": [196]})
        assert len(videos) == 1
        video = videos[0]
        assert video.video_id == 196
        assert video.filename

        # Fetch videos with all fields (include=None means everything)
        videos_full = disk_database.get_videos(include=None, where={"video_id": [196]})
        assert len(videos_full) == 1
        video_full = videos_full[0]
        assert hasattr(video_full, "errors")
        assert hasattr(video_full, "audio_languages")
        assert hasattr(video_full, "properties")

    def test_get_videos_with_thumbnail_fields(self, disk_database):
        """Test fetching videos with thumbnail-related fields."""
        # Fetch videos requesting thumbnail fields (include=None gets all)
        videos = disk_database.get_videos(include=None, where={"video_id": [196]})
        assert len(videos) == 1
        video = videos[0]
        assert video.video_id == 196
        # Thumbnail fields should be present
        assert hasattr(video, "thumbnail")
        assert hasattr(video, "with_thumbnails")

    def test_get_videos_with_errors(self, disk_database):
        """Test fetching videos with errors."""
        # Fetch unreadable videos (readable=False)
        # include=["errors"] to specifically request error data
        videos = disk_database.get_videos(include=["errors"], where={"readable": False})
        assert len(videos) >= 3
        # Verify errors attribute exists
        for video in videos:
            assert hasattr(video, "errors")
            assert isinstance(video.errors, (list, set))

    def test_get_videos_with_languages(self, disk_database):
        """Test fetching videos with audio/subtitle languages."""
        # Fetch videos with language information
        videos = disk_database.get_videos(
            include=["audio_languages", "subtitle_languages"], where={"video_id": [196]}
        )
        assert len(videos) == 1
        video = videos[0]
        assert hasattr(video, "audio_languages")
        assert hasattr(video, "subtitle_languages")

    def test_get_videos_with_properties(self, disk_database):
        """Test fetching videos with properties."""
        # Fetch videos with properties
        videos = disk_database.get_videos(
            include=["properties"], where={"video_id": [196]}
        )
        assert len(videos) == 1
        video = videos[0]
        assert hasattr(video, "properties")
        assert isinstance(video.properties, dict)


class TestProviderEdgeCases:
    """Tests for edge cases in video querying."""

    def _query_ids(self, db, view) -> list[int]:
        return [v.video_id for v in db.query_videos(view, None, None).result]

    def test_provider_empty_results(self, disk_database):
        """Test query with filters that return no results."""
        view = ViewContext()
        view.set_sources([["not_found"], ["unreadable"]])
        view.set_search("this_text_definitely_does_not_exist", "exact")
        assert len(self._query_ids(disk_database, view)) == 0

    def test_provider_multiple_sources_or_logic(self, disk_database):
        """Test query with multiple sources (OR logic)."""
        view = ViewContext()
        view.set_sources([["not_found"], ["unreadable"]])
        indices = self._query_ids(disk_database, view)
        assert len(indices) >= 3

    def test_provider_grouping_with_empty_results(self, disk_database):
        """Test grouping when no videos match."""
        view = ViewContext()
        view.set_sources([["readable", "without_thumbnails"]])
        view.set_grouping("audio_bit_rate")
        assert len(self._query_ids(disk_database, view)) == 0
        stats = disk_database.query_videos(view, 1, 0).classifier_stats
        assert len(stats) == 0

    def test_provider_classifier_multiple_levels(self, disk_database):
        """Test classifier with multiple classification levels."""
        view = ViewContext()
        view.set_grouping(
            "category",
            is_property=True,
            sorting="count",
            reverse=True,
            allow_singletons=True,
        )
        view.classifier = ["vertical"]
        indices = self._query_ids(disk_database, view)
        assert len(indices) == 7

        view.classifier = ["vertical", "e"]
        indices = self._query_ids(disk_database, view)
        assert len(indices) == 3

    def test_provider_search_modes(self, disk_database):
        """Test different search modes (and, or, exact)."""
        view = ViewContext()
        view.set_search("unknown audio", "and")
        and_count = len(self._query_ids(disk_database, view))

        view.set_search("unknown audio", "or")
        or_count = len(self._query_ids(disk_database, view))
        assert or_count >= and_count

        view.set_search("unknown audio codec", "exact")
        exact_count = len(self._query_ids(disk_database, view))
        assert exact_count <= and_count


class TestDatabaseCRUDOperations:
    """Tests for database CRUD operations (Create, Read, Update, Delete)."""

    def _query_ids(self, db, view) -> list[int]:
        return [v.video_id for v in db.query_videos(view, None, None).result]

    def test_video_property_modification(self, memory_database):
        """Test modifying video properties."""
        # Get initial property value
        initial_values = memory_database.videos_tag_get("category", [196])[196]
        initial_count = len(initial_values)

        # Add a new property value
        new_values = list(initial_values) + ["test_category"]
        memory_database.videos_tag_set("category", {196: new_values})

        # Verify the change
        updated_values = memory_database.videos_tag_get("category", [196])[196]
        assert len(updated_values) == initial_count + 1
        assert "test_category" in updated_values

        # Restore original values
        memory_database.videos_tag_set("category", {196: initial_values})
        restored_values = memory_database.videos_tag_get("category", [196])[196]
        assert restored_values == initial_values

    def test_query_videos_after_modification(self, memory_database):
        """Test query_videos reflects database modifications."""
        db = memory_database
        view = ViewContext()
        view.set_search("palm beach", "exact")
        initial_count = len(self._query_ids(db, view))

        old_values = db.videos_tag_get("category", [196])[196]
        new_values = list(old_values) + ["palm beach"]
        db.videos_tag_set("category", {196: new_values})

        new_count = len(self._query_ids(db, view))
        assert new_count > initial_count

        db.videos_tag_set("category", {196: old_values})

    def test_get_videos_by_multiple_ids(self, disk_database):
        """Test fetching multiple videos by IDs."""
        video_ids = [196, 114, 200]
        videos = disk_database.get_videos(include=(), where={"video_id": video_ids})
        # We should get at least the videos that exist
        assert len(videos) > 0
        fetched_ids = [v.video_id for v in videos]
        # All fetched IDs should be in the requested list
        assert all(vid in video_ids for vid in fetched_ids)

    def test_get_videos_with_filename_filter(self, disk_database):
        """Test fetching videos with filename filter."""
        # Get a specific video first to know its filename
        videos = disk_database.get_videos(where={"video_id": [196]})
        assert len(videos) == 1
        filename = videos[0].filename

        # Now fetch by filename
        videos_by_filename = disk_database.get_videos(where={"filename": filename})
        assert len(videos_by_filename) == 1
        assert videos_by_filename[0].video_id == 196
