"""
Tests comparing video provider behavior between JSON and NewSQL databases.

These tests ensure that the JsonDatabaseVideoProvider behaves consistently
regardless of whether it's backed by JsonDatabase or NewSqlDatabase.
"""

import pytest

from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.newsql.newsql_database import NewSqlDatabase
from pysaurus.video.video_sorting import VideoSorting


# =============================================================================
# Helper functions
# =============================================================================


def get_all_video_ids(db: AbstractDatabase) -> list[int]:
    """Get all video IDs from a database."""
    return [v.video_id for v in db.get_videos(include=["video_id"])]


def get_readable_video_ids(db: AbstractDatabase) -> list[int]:
    """Get all readable video IDs from a database."""
    return [
        v.video_id
        for v in db.get_videos(include=["video_id"], where={"readable": True})
    ]


def get_video_filenames(db: AbstractDatabase) -> dict[int, str]:
    """Get mapping of video_id -> filename for all videos."""
    return {
        v.video_id: v.filename.path
        for v in db.get_videos(include=["video_id", "filename"])
    }


# =============================================================================
# jsondb_provider_search tests
# =============================================================================


class TestProviderSearch:
    """Tests for jsondb_provider_search consistency."""

    def test_search_empty_text_returns_empty(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Empty search text should return empty results."""
        old_result = list(fake_old_database.jsondb_provider_search("", "and"))
        new_result = list(fake_new_database.jsondb_provider_search("", "and"))
        assert old_result == new_result == []

    def test_search_by_id(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Search by ID should find the video."""
        # Get a sample video ID
        videos = fake_old_database.get_videos(include=["video_id"])
        if not videos:
            pytest.skip("No videos in database")

        video_id = videos[0].video_id
        old_result = list(fake_old_database.jsondb_provider_search(str(video_id), "id"))
        new_result = list(fake_new_database.jsondb_provider_search(str(video_id), "id"))
        assert old_result == new_result == [video_id]

    def test_search_by_id_not_found(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Search by non-existent ID should return empty."""
        old_result = list(fake_old_database.jsondb_provider_search("999999999", "id"))
        new_result = list(fake_new_database.jsondb_provider_search("999999999", "id"))
        assert old_result == new_result == []

    def test_search_and_condition(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Search with AND condition should match all terms."""
        # Use "test" which should be in the filename of test videos
        old_result = set(fake_old_database.jsondb_provider_search("test", "and"))
        new_result = set(fake_new_database.jsondb_provider_search("test", "and"))
        assert old_result == new_result

    def test_search_or_condition(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Search with OR condition should match any term."""
        old_result = set(fake_old_database.jsondb_provider_search("test", "or"))
        new_result = set(fake_new_database.jsondb_provider_search("test", "or"))
        assert old_result == new_result

    def test_search_with_multiple_words_and(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Search with multiple words and AND condition."""
        old_result = set(fake_old_database.jsondb_provider_search("test 000001", "and"))
        new_result = set(fake_new_database.jsondb_provider_search("test 000001", "and"))
        assert old_result == new_result

    def test_search_with_multiple_words_or(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Search with multiple words and OR condition."""
        old_result = set(
            fake_old_database.jsondb_provider_search("action comedy", "or")
        )
        new_result = set(
            fake_new_database.jsondb_provider_search("action comedy", "or")
        )
        assert old_result == new_result

    def test_search_exact_condition(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Search with exact match condition."""
        old_result = set(
            fake_old_database.jsondb_provider_search("test_000001", "exact")
        )
        new_result = set(
            fake_new_database.jsondb_provider_search("test_000001", "exact")
        )
        assert old_result == new_result

    def test_search_filtered_by_video_ids(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Search filtered by specific video IDs."""
        # Get first 100 video IDs
        all_ids = get_all_video_ids(fake_old_database)[:100]
        if not all_ids:
            pytest.skip("No videos in database")

        old_result = set(
            fake_old_database.jsondb_provider_search("test", "and", all_ids)
        )
        new_result = set(
            fake_new_database.jsondb_provider_search("test", "and", all_ids)
        )
        assert old_result == new_result
        # Result should be subset of the filter
        assert old_result.issubset(set(all_ids))

    def test_search_by_category_folder(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Search by category (folder name in path)."""
        old_result = set(fake_old_database.jsondb_provider_search("action", "and"))
        new_result = set(fake_new_database.jsondb_provider_search("action", "and"))
        assert old_result == new_result

    def test_search_case_insensitive(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Search should be case insensitive."""
        old_lower = set(fake_old_database.jsondb_provider_search("test", "and"))
        old_upper = set(fake_old_database.jsondb_provider_search("TEST", "and"))
        new_lower = set(fake_new_database.jsondb_provider_search("test", "and"))
        new_upper = set(fake_new_database.jsondb_provider_search("TEST", "and"))
        # Both should return the same results regardless of case
        assert old_lower == old_upper
        assert new_lower == new_upper
        assert old_lower == new_lower


# =============================================================================
# jsondb_provider_sort_video_indices tests
# =============================================================================


class TestProviderSort:
    """Tests for jsondb_provider_sort_video_indices consistency."""

    def test_sort_by_title_asc(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Sort by title ascending."""
        video_ids = get_all_video_ids(fake_old_database)[:100]
        sorting = VideoSorting(["title"])

        old_result = fake_old_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        new_result = fake_new_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        assert old_result == new_result

    def test_sort_by_title_desc(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Sort by title descending."""
        video_ids = get_all_video_ids(fake_old_database)[:100]
        sorting = VideoSorting(["-title"])

        old_result = fake_old_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        new_result = fake_new_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        assert old_result == new_result

    def test_sort_by_file_size(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Sort by file size."""
        video_ids = get_all_video_ids(fake_old_database)[:100]
        sorting = VideoSorting(["file_size"])

        old_result = fake_old_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        new_result = fake_new_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        assert old_result == new_result

    def test_sort_by_duration(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Sort by duration."""
        video_ids = get_readable_video_ids(fake_old_database)[:100]
        if not video_ids:
            pytest.skip("No readable videos")
        sorting = VideoSorting(["duration"])

        old_result = fake_old_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        new_result = fake_new_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        assert old_result == new_result

    def test_sort_by_width(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Sort by video width."""
        video_ids = get_readable_video_ids(fake_old_database)[:100]
        if not video_ids:
            pytest.skip("No readable videos")
        sorting = VideoSorting(["width"])

        old_result = fake_old_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        new_result = fake_new_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        assert old_result == new_result

    def test_sort_by_height(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Sort by video height."""
        video_ids = get_readable_video_ids(fake_old_database)[:100]
        if not video_ids:
            pytest.skip("No readable videos")
        sorting = VideoSorting(["height"])

        old_result = fake_old_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        new_result = fake_new_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        assert old_result == new_result

    def test_sort_by_video_id(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Sort by video ID."""
        video_ids = get_all_video_ids(fake_old_database)[:100]
        sorting = VideoSorting(["video_id"])

        old_result = fake_old_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        new_result = fake_new_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        assert old_result == new_result

    def test_sort_by_filename(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Sort by filename."""
        video_ids = get_all_video_ids(fake_old_database)[:100]
        sorting = VideoSorting(["filename"])

        old_result = fake_old_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        new_result = fake_new_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        assert old_result == new_result

    def test_sort_multi_field(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Sort by multiple fields."""
        video_ids = get_all_video_ids(fake_old_database)[:100]
        sorting = VideoSorting(["width", "height", "title"])

        old_result = fake_old_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        new_result = fake_new_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        assert old_result == new_result

    def test_sort_preserves_ids(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Sorting should preserve all input IDs (just reorder)."""
        video_ids = get_all_video_ids(fake_old_database)[:100]
        sorting = VideoSorting(["title"])

        old_result = fake_old_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        new_result = fake_new_database.jsondb_provider_sort_video_indices(
            video_ids, sorting
        )
        assert set(old_result) == set(video_ids)
        assert set(new_result) == set(video_ids)

    def test_sort_empty_list(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Sorting empty list should return empty list."""
        sorting = VideoSorting(["title"])

        old_result = fake_old_database.jsondb_provider_sort_video_indices([], sorting)
        new_result = fake_new_database.jsondb_provider_sort_video_indices([], sorting)
        assert old_result == new_result == []


# =============================================================================
# Thumbnail method tests
# =============================================================================


class TestThumbnailMethods:
    """Tests for thumbnail-related jsondb methods."""

    def test_has_thumbnail_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """jsondb_has_thumbnail should return same results."""
        filenames = get_video_filenames(fake_old_database)
        sample_filenames = list(filenames.values())[:100]

        for filename in sample_filenames:
            from pysaurus.core.absolute_path import AbsolutePath

            path = AbsolutePath(filename)
            old_has = fake_old_database.jsondb_has_thumbnail(path)
            new_has = fake_new_database.jsondb_has_thumbnail(path)
            assert old_has == new_has, f"Mismatch for {filename}"

    def test_get_thumbnail_base64_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """jsondb_get_thumbnail_base64 should return same results."""
        filenames = get_video_filenames(fake_old_database)
        sample_filenames = list(filenames.values())[
            :20
        ]  # Fewer samples as base64 is larger

        for filename in sample_filenames:
            from pysaurus.core.absolute_path import AbsolutePath

            path = AbsolutePath(filename)
            old_b64 = fake_old_database.jsondb_get_thumbnail_base64(path)
            new_b64 = fake_new_database.jsondb_get_thumbnail_base64(path)
            assert old_b64 == new_b64, f"Mismatch for {filename}"

    def test_get_thumbnail_blob_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """jsondb_get_thumbnail_blob should return same results."""
        filenames = get_video_filenames(fake_old_database)
        sample_filenames = list(filenames.values())[:20]

        for filename in sample_filenames:
            from pysaurus.core.absolute_path import AbsolutePath

            path = AbsolutePath(filename)
            old_blob = fake_old_database.jsondb_get_thumbnail_blob(path)
            new_blob = fake_new_database.jsondb_get_thumbnail_blob(path)
            assert old_blob == new_blob, f"Mismatch for {filename}"

    def test_thumbnail_count_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """Total number of videos with thumbnails should match."""
        filenames = get_video_filenames(fake_old_database)

        old_count = sum(
            1
            for fn in filenames.values()
            if fake_old_database.jsondb_has_thumbnail(
                __import__(
                    "pysaurus.core.absolute_path", fromlist=["AbsolutePath"]
                ).AbsolutePath(fn)
            )
        )
        new_count = sum(
            1
            for fn in filenames.values()
            if fake_new_database.jsondb_has_thumbnail(
                __import__(
                    "pysaurus.core.absolute_path", fromlist=["AbsolutePath"]
                ).AbsolutePath(fn)
            )
        )
        assert old_count == new_count


# =============================================================================
# jsondb_prop_val_is_default tests
# =============================================================================


class TestPropValIsDefault:
    """Tests for jsondb_prop_val_is_default consistency."""

    def test_prop_val_is_default_for_string_prop(
        self, mem_old_database: AbstractDatabase, mem_new_database: NewSqlDatabase
    ):
        """Check default value detection for string properties."""
        # Create a test property
        mem_old_database.prop_type_add("test_str_prop", "str", "", False)
        mem_new_database.prop_type_add("test_str_prop", "str", "", False)

        # Empty list should be default for non-multiple
        assert mem_old_database.jsondb_prop_val_is_default(
            "test_str_prop", [""]
        ) == mem_new_database.jsondb_prop_val_is_default("test_str_prop", [""])

        # Non-empty should not be default
        assert mem_old_database.jsondb_prop_val_is_default(
            "test_str_prop", ["hello"]
        ) == mem_new_database.jsondb_prop_val_is_default("test_str_prop", ["hello"])

    def test_prop_val_is_default_for_int_prop(
        self, mem_old_database: AbstractDatabase, mem_new_database: NewSqlDatabase
    ):
        """Check default value detection for integer properties."""
        mem_old_database.prop_type_add("test_int_prop", "int", 0, False)
        mem_new_database.prop_type_add("test_int_prop", "int", 0, False)

        assert mem_old_database.jsondb_prop_val_is_default(
            "test_int_prop", [0]
        ) == mem_new_database.jsondb_prop_val_is_default("test_int_prop", [0])

        assert mem_old_database.jsondb_prop_val_is_default(
            "test_int_prop", [42]
        ) == mem_new_database.jsondb_prop_val_is_default("test_int_prop", [42])

    def test_prop_val_is_default_for_multiple_prop(
        self, mem_old_database: AbstractDatabase, mem_new_database: NewSqlDatabase
    ):
        """Check default value detection for multiple-value properties."""
        mem_old_database.prop_type_add("test_multi_prop", "str", "", True)
        mem_new_database.prop_type_add("test_multi_prop", "str", "", True)

        # Empty list is default for multiple
        assert mem_old_database.jsondb_prop_val_is_default(
            "test_multi_prop", []
        ) == mem_new_database.jsondb_prop_val_is_default("test_multi_prop", [])

        # Non-empty is not default
        assert mem_old_database.jsondb_prop_val_is_default(
            "test_multi_prop", ["a", "b"]
        ) == mem_new_database.jsondb_prop_val_is_default("test_multi_prop", ["a", "b"])

    def test_prop_val_is_default_for_enum_prop(
        self, mem_old_database: AbstractDatabase, mem_new_database: NewSqlDatabase
    ):
        """Check default value detection for enum properties."""
        mem_old_database.prop_type_add("test_enum_prop", "str", ["A", "B", "C"], False)
        mem_new_database.prop_type_add("test_enum_prop", "str", ["A", "B", "C"], False)

        # First enum value is default
        assert mem_old_database.jsondb_prop_val_is_default(
            "test_enum_prop", ["A"]
        ) == mem_new_database.jsondb_prop_val_is_default("test_enum_prop", ["A"])

        # Non-first value is not default
        assert mem_old_database.jsondb_prop_val_is_default(
            "test_enum_prop", ["B"]
        ) == mem_new_database.jsondb_prop_val_is_default("test_enum_prop", ["B"])


# =============================================================================
# Video provider pipeline layer tests (via get_videos with sources)
# =============================================================================


class TestProviderLayerSource:
    """Tests for LayerSource behavior consistency."""

    def test_source_readable_videos(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """LayerSource with 'readable' source."""
        old_videos = set(
            v.video_id
            for v in fake_old_database.get_videos(
                include=["video_id"], where={"readable": True}
            )
        )
        new_videos = set(
            v.video_id
            for v in fake_new_database.get_videos(
                include=["video_id"], where={"readable": True}
            )
        )
        assert old_videos == new_videos

    def test_source_found_videos(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """LayerSource with 'found' source."""
        old_videos = set(
            v.video_id
            for v in fake_old_database.get_videos(
                include=["video_id"], where={"found": True}
            )
        )
        new_videos = set(
            v.video_id
            for v in fake_new_database.get_videos(
                include=["video_id"], where={"found": True}
            )
        )
        assert old_videos == new_videos

    def test_source_not_found_videos(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """LayerSource with 'not_found' source."""
        old_videos = set(
            v.video_id
            for v in fake_old_database.get_videos(
                include=["video_id"], where={"not_found": True}
            )
        )
        new_videos = set(
            v.video_id
            for v in fake_new_database.get_videos(
                include=["video_id"], where={"not_found": True}
            )
        )
        assert old_videos == new_videos

    def test_source_with_thumbnails(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """LayerSource with 'with_thumbnails' source."""
        old_videos = set(
            v.video_id
            for v in fake_old_database.get_videos(
                include=["video_id"], where={"with_thumbnails": True}
            )
        )
        new_videos = set(
            v.video_id
            for v in fake_new_database.get_videos(
                include=["video_id"], where={"with_thumbnails": True}
            )
        )
        assert old_videos == new_videos

    def test_source_without_thumbnails(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """LayerSource with 'without_thumbnails' source."""
        old_videos = set(
            v.video_id
            for v in fake_old_database.get_videos(
                include=["video_id"], where={"without_thumbnails": True}
            )
        )
        new_videos = set(
            v.video_id
            for v in fake_new_database.get_videos(
                include=["video_id"], where={"without_thumbnails": True}
            )
        )
        assert old_videos == new_videos


# =============================================================================
# SqlVideo attribute consistency tests
# =============================================================================


class TestSqlVideoAttributes:
    """Tests ensuring SqlVideo attributes match LazyVideo attributes."""

    def test_video_id_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """video_id should be identical."""
        old_ids = sorted(
            v.video_id for v in fake_old_database.get_videos(include=["video_id"])
        )
        new_ids = sorted(
            v.video_id for v in fake_new_database.get_videos(include=["video_id"])
        )
        assert old_ids == new_ids

    def test_filename_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """filename should be identical."""
        old_filenames = {
            v.video_id: str(v.filename) for v in fake_old_database.get_videos()
        }
        new_filenames = {
            v.video_id: str(v.filename) for v in fake_new_database.get_videos()
        }
        assert old_filenames == new_filenames

    def test_file_size_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """file_size should be identical."""
        old_sizes = {v.video_id: v.file_size for v in fake_old_database.get_videos()}
        new_sizes = {v.video_id: v.file_size for v in fake_new_database.get_videos()}
        assert old_sizes == new_sizes

    def test_duration_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """duration should be identical for readable videos."""
        old_data = {
            v.video_id: v.duration
            for v in fake_old_database.get_videos(where={"readable": True})
        }
        new_data = {
            v.video_id: v.duration
            for v in fake_new_database.get_videos(where={"readable": True})
        }
        assert old_data == new_data

    def test_width_height_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """width and height should be identical."""
        old_data = {
            v.video_id: (v.width, v.height)
            for v in fake_old_database.get_videos(where={"readable": True})
        }
        new_data = {
            v.video_id: (v.width, v.height)
            for v in fake_new_database.get_videos(where={"readable": True})
        }
        assert old_data == new_data

    def test_codec_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """video_codec and audio_codec should be identical."""
        old_data = {
            v.video_id: (str(v.video_codec), str(v.audio_codec))
            for v in fake_old_database.get_videos(where={"readable": True})
        }
        new_data = {
            v.video_id: (str(v.video_codec), str(v.audio_codec))
            for v in fake_new_database.get_videos(where={"readable": True})
        }
        assert old_data == new_data

    def test_container_format_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """container_format should be identical."""
        old_data = {
            v.video_id: str(v.container_format)
            for v in fake_old_database.get_videos(where={"readable": True})
        }
        new_data = {
            v.video_id: str(v.container_format)
            for v in fake_new_database.get_videos(where={"readable": True})
        }
        assert old_data == new_data

    def test_title_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """title should be identical."""
        old_data = {v.video_id: str(v.title) for v in fake_old_database.get_videos()}
        new_data = {v.video_id: str(v.title) for v in fake_new_database.get_videos()}
        assert old_data == new_data

    def test_extension_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """extension should be identical."""
        old_data = {v.video_id: v.extension for v in fake_old_database.get_videos()}
        new_data = {v.video_id: v.extension for v in fake_new_database.get_videos()}
        assert old_data == new_data

    def test_readable_unreadable_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """readable/unreadable flags should be identical."""
        old_data = {
            v.video_id: (v.readable, v.unreadable)
            for v in fake_old_database.get_videos()
        }
        new_data = {
            v.video_id: (v.readable, v.unreadable)
            for v in fake_new_database.get_videos()
        }
        assert old_data == new_data

    def test_found_not_found_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """found/not_found flags should be identical."""
        old_data = {
            v.video_id: (v.found, v.not_found) for v in fake_old_database.get_videos()
        }
        new_data = {
            v.video_id: (v.found, v.not_found) for v in fake_new_database.get_videos()
        }
        assert old_data == new_data

    def test_with_thumbnails_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """with_thumbnails/without_thumbnails should be identical."""
        old_data = {
            v.video_id: (v.with_thumbnails, v.without_thumbnails)
            for v in fake_old_database.get_videos()
        }
        new_data = {
            v.video_id: (v.with_thumbnails, v.without_thumbnails)
            for v in fake_new_database.get_videos()
        }
        assert old_data == new_data

    def test_properties_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """properties dict should be identical."""
        old_data = {v.video_id: v.properties for v in fake_old_database.get_videos()}
        new_data = {v.video_id: v.properties for v in fake_new_database.get_videos()}
        assert old_data == new_data

    def test_similarity_id_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """similarity_id should be identical."""
        old_data = {v.video_id: v.similarity_id for v in fake_old_database.get_videos()}
        new_data = {v.video_id: v.similarity_id for v in fake_new_database.get_videos()}
        assert old_data == new_data

    def test_frame_rate_consistency(
        self, fake_old_database: AbstractDatabase, fake_new_database: NewSqlDatabase
    ):
        """frame_rate_num/frame_rate_den should be identical."""
        old_data = {
            v.video_id: (v.frame_rate_num, v.frame_rate_den)
            for v in fake_old_database.get_videos(where={"readable": True})
        }
        new_data = {
            v.video_id: (v.frame_rate_num, v.frame_rate_den)
            for v in fake_new_database.get_videos(where={"readable": True})
        }
        assert old_data == new_data
