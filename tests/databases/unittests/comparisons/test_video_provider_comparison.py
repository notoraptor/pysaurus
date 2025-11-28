"""
Tests comparing video provider behavior between JSON and NewSQL databases.

These tests ensure that the video provider behaves consistently regardless of
whether it's backed by JsonDatabase or NewSqlDatabase.

All tests use the PUBLIC provider API (database.provider.*) rather than
internal jsondb_* methods, making them implementation-independent.
"""

import pytest

from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.newsql.newsql_database import NewSqlDatabase


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def old_provider(fake_old_database: AbstractDatabase):
    """Get provider from JSON database, reset before each test."""
    provider = fake_old_database.provider
    provider.reset()
    return provider


@pytest.fixture
def new_provider(fake_new_database: NewSqlDatabase):
    """Get provider from SQL database, reset before each test."""
    provider = fake_new_database.provider
    provider.reset()
    return provider


# =============================================================================
# Helper functions
# =============================================================================


def get_view_ids(provider) -> list[int]:
    """Get video IDs from provider's current view."""
    return list(provider.get_view_indices())


def get_view_ids_set(provider) -> set[int]:
    """Get video IDs from provider's current view as a set."""
    return set(provider.get_view_indices())


# =============================================================================
# Source layer tests
# =============================================================================


class TestProviderSource:
    """Tests for provider.set_sources() behavior."""

    def test_default_source_readable(self, old_provider, new_provider):
        """Default source should be readable videos."""
        # Default is [["readable"]]
        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids
        assert len(old_ids) > 0

    def test_source_readable(self, old_provider, new_provider):
        """Set source to readable videos explicitly."""
        old_provider.set_sources([["readable"]])
        new_provider.set_sources([["readable"]])

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

    def test_source_found(self, old_provider, new_provider):
        """Set source to found videos."""
        old_provider.set_sources([["found"]])
        new_provider.set_sources([["found"]])

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

    def test_source_with_thumbnails(self, old_provider, new_provider):
        """Set source to videos with thumbnails."""
        old_provider.set_sources([["with_thumbnails"]])
        new_provider.set_sources([["with_thumbnails"]])

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

    def test_source_without_thumbnails(self, old_provider, new_provider):
        """Set source to videos without thumbnails."""
        old_provider.set_sources([["without_thumbnails"]])
        new_provider.set_sources([["without_thumbnails"]])

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

    def test_source_multiple_flags(self, old_provider, new_provider):
        """Set source with multiple flags (AND condition)."""
        old_provider.set_sources([["readable", "found"]])
        new_provider.set_sources([["readable", "found"]])

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

    def test_source_multiple_paths(self, old_provider, new_provider):
        """Set source with multiple paths (OR condition)."""
        old_provider.set_sources([["readable"], ["not_found"]])
        new_provider.set_sources([["readable"], ["not_found"]])

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

    def test_count_source_videos(self, old_provider, new_provider):
        """count_source_videos() should return same count."""
        old_provider.set_sources([["readable"]])
        new_provider.set_sources([["readable"]])

        # Trigger view computation
        old_provider.get_view_indices()
        new_provider.get_view_indices()

        assert old_provider.count_source_videos() == new_provider.count_source_videos()


# =============================================================================
# Search layer tests
# =============================================================================


class TestProviderSearch:
    """Tests for provider.set_search() behavior."""

    def test_search_empty(self, old_provider, new_provider):
        """Empty search should return all source videos."""
        old_provider.set_search("")
        new_provider.set_search("")

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids
        assert len(old_ids) > 0

    def test_search_and_single_term(self, old_provider, new_provider):
        """Search with AND condition, single term."""
        old_provider.set_search("test", "and")
        new_provider.set_search("test", "and")

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

    def test_search_and_multiple_terms(self, old_provider, new_provider):
        """Search with AND condition, multiple terms."""
        old_provider.set_search("test 000001", "and")
        new_provider.set_search("test 000001", "and")

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

    def test_search_or_condition(self, old_provider, new_provider):
        """Search with OR condition."""
        old_provider.set_search("action comedy", "or")
        new_provider.set_search("action comedy", "or")

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

    def test_search_exact_condition(self, old_provider, new_provider):
        """Search with exact match condition."""
        old_provider.set_search("test_000001", "exact")
        new_provider.set_search("test_000001", "exact")

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

    def test_search_by_id(self, old_provider, new_provider, fake_old_database):
        """Search by video ID."""
        # Get a sample video ID
        videos = fake_old_database.get_videos(include=["video_id"])
        if not videos:
            pytest.skip("No videos in database")

        video_id = videos[0].video_id

        old_provider.set_search(str(video_id), "id")
        new_provider.set_search(str(video_id), "id")

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids == [video_id]

    def test_search_by_id_not_found(self, old_provider, new_provider):
        """Search by non-existent ID should return empty."""
        old_provider.set_search("999999999", "id")
        new_provider.set_search("999999999", "id")

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids == []

    def test_search_case_insensitive(self, old_provider, new_provider):
        """Search should be case insensitive."""
        old_provider.set_search("TEST", "and")
        new_provider.set_search("TEST", "and")
        old_upper = get_view_ids_set(old_provider)
        new_upper = get_view_ids_set(new_provider)

        old_provider.set_search("test", "and")
        new_provider.set_search("test", "and")
        old_lower = get_view_ids_set(old_provider)
        new_lower = get_view_ids_set(new_provider)

        assert old_upper == old_lower
        assert new_upper == new_lower
        assert old_upper == new_upper

    def test_search_by_category(self, old_provider, new_provider):
        """Search by category folder name."""
        old_provider.set_search("action", "and")
        new_provider.set_search("action", "and")

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

    def test_search_no_results(self, old_provider, new_provider):
        """Search with no matching results."""
        old_provider.set_search("xyznonexistent123", "and")
        new_provider.set_search("xyznonexistent123", "and")

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids == []


# =============================================================================
# Sort layer tests
# =============================================================================


class TestProviderSort:
    """Tests for provider.set_sort() behavior."""

    def test_sort_by_title_asc(self, old_provider, new_provider):
        """Sort by title ascending."""
        old_provider.set_sort(["title"])
        new_provider.set_sort(["title"])

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids

    def test_sort_by_title_desc(self, old_provider, new_provider):
        """Sort by title descending."""
        old_provider.set_sort(["-title"])
        new_provider.set_sort(["-title"])

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids

    def test_sort_by_file_size(self, old_provider, new_provider):
        """Sort by file size."""
        old_provider.set_sort(["file_size"])
        new_provider.set_sort(["file_size"])

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids

    def test_sort_by_file_size_desc(self, old_provider, new_provider):
        """Sort by file size descending."""
        old_provider.set_sort(["-file_size"])
        new_provider.set_sort(["-file_size"])

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids

    def test_sort_by_duration(self, old_provider, new_provider):
        """Sort by duration."""
        old_provider.set_sort(["duration"])
        new_provider.set_sort(["duration"])

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids

    def test_sort_by_width(self, old_provider, new_provider):
        """Sort by video width."""
        old_provider.set_sort(["width"])
        new_provider.set_sort(["width"])

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids

    def test_sort_by_height(self, old_provider, new_provider):
        """Sort by video height."""
        old_provider.set_sort(["height"])
        new_provider.set_sort(["height"])

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids

    def test_sort_by_video_id(self, old_provider, new_provider):
        """Sort by video ID."""
        old_provider.set_sort(["video_id"])
        new_provider.set_sort(["video_id"])

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids

    def test_sort_by_filename(self, old_provider, new_provider):
        """Sort by filename."""
        old_provider.set_sort(["filename"])
        new_provider.set_sort(["filename"])

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids

    def test_sort_multi_field(self, old_provider, new_provider):
        """Sort by multiple fields."""
        old_provider.set_sort(["width", "height", "title"])
        new_provider.set_sort(["width", "height", "title"])

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids

    def test_sort_multi_field_mixed_order(self, old_provider, new_provider):
        """Sort by multiple fields with mixed asc/desc."""
        old_provider.set_sort(["width", "-height", "title"])
        new_provider.set_sort(["width", "-height", "title"])

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids

    def test_sort_preserves_count(self, old_provider, new_provider):
        """Sorting should preserve all video IDs (just reorder)."""
        old_provider.set_sort(["title"])
        new_provider.set_sort(["title"])

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)

        # Reset to default sort and compare counts
        old_provider.set_sort(["+title"])
        new_provider.set_sort(["+title"])

        old_default = get_view_ids_set(old_provider)
        new_default = get_view_ids_set(new_provider)

        assert old_ids == old_default
        assert new_ids == new_default


# =============================================================================
# Grouping layer tests
# =============================================================================


class TestProviderGrouping:
    """Tests for provider.set_groups() behavior."""

    def test_no_grouping(self, old_provider, new_provider):
        """No grouping should return all videos in one group."""
        old_provider.set_groups(None)
        new_provider.set_groups(None)

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

    def test_group_by_extension(self, old_provider, new_provider):
        """Group by file extension."""
        old_provider.set_groups("extension", is_property=False, allow_singletons=True)
        new_provider.set_groups("extension", is_property=False, allow_singletons=True)

        # Get classifier stats (group info)
        old_provider.get_view_indices()
        new_provider.get_view_indices()

        old_stats = old_provider.get_classifier_stats()
        new_stats = new_provider.get_classifier_stats()

        # Compare group values and counts
        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {s.value: s.count for s in new_stats}
        assert old_groups == new_groups

    def test_group_by_width(self, old_provider, new_provider):
        """Group by video width."""
        old_provider.set_groups("width", is_property=False, allow_singletons=True)
        new_provider.set_groups("width", is_property=False, allow_singletons=True)

        old_provider.get_view_indices()
        new_provider.get_view_indices()

        old_stats = old_provider.get_classifier_stats()
        new_stats = new_provider.get_classifier_stats()

        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {s.value: s.count for s in new_stats}
        assert old_groups == new_groups

    def test_group_by_height(self, old_provider, new_provider):
        """Group by video height."""
        old_provider.set_groups("height", is_property=False, allow_singletons=True)
        new_provider.set_groups("height", is_property=False, allow_singletons=True)

        old_provider.get_view_indices()
        new_provider.get_view_indices()

        old_stats = old_provider.get_classifier_stats()
        new_stats = new_provider.get_classifier_stats()

        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {s.value: s.count for s in new_stats}
        assert old_groups == new_groups

    def test_group_sorting_by_count(self, old_provider, new_provider):
        """Groups sorted by count."""
        old_provider.set_groups(
            "extension",
            is_property=False,
            sorting="count",
            reverse=True,
            allow_singletons=True,
        )
        new_provider.set_groups(
            "extension",
            is_property=False,
            sorting="count",
            reverse=True,
            allow_singletons=True,
        )

        old_provider.get_view_indices()
        new_provider.get_view_indices()

        old_stats = old_provider.get_classifier_stats()
        new_stats = new_provider.get_classifier_stats()

        # Check order is the same
        old_values = [s.value for s in old_stats]
        new_values = [s.value for s in new_stats]
        assert old_values == new_values

    def test_group_sorting_by_field(self, old_provider, new_provider):
        """Groups sorted by field value."""
        old_provider.set_groups(
            "extension",
            is_property=False,
            sorting="field",
            reverse=False,
            allow_singletons=True,
        )
        new_provider.set_groups(
            "extension",
            is_property=False,
            sorting="field",
            reverse=False,
            allow_singletons=True,
        )

        old_provider.get_view_indices()
        new_provider.get_view_indices()

        old_stats = old_provider.get_classifier_stats()
        new_stats = new_provider.get_classifier_stats()

        old_values = [s.value for s in old_stats]
        new_values = [s.value for s in new_stats]
        assert old_values == new_values

    def test_select_group(self, old_provider, new_provider):
        """Select a specific group."""
        old_provider.set_groups("extension", is_property=False, allow_singletons=True)
        new_provider.set_groups("extension", is_property=False, allow_singletons=True)

        # Get first group
        old_provider.set_group(0)
        new_provider.set_group(0)

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

        # Get second group (if exists)
        old_provider.get_view_indices()
        stats = old_provider.get_classifier_stats()
        if len(stats) > 1:
            old_provider.set_group(1)
            new_provider.set_group(1)

            old_ids = get_view_ids_set(old_provider)
            new_ids = get_view_ids_set(new_provider)
            assert old_ids == new_ids


# =============================================================================
# Combined layer tests (source + search + sort)
# =============================================================================


class TestProviderCombined:
    """Tests for combined layer operations."""

    def test_source_then_search(self, old_provider, new_provider):
        """Set source, then search within it."""
        old_provider.set_sources([["readable"]])
        old_provider.set_search("action", "and")
        new_provider.set_sources([["readable"]])
        new_provider.set_search("action", "and")

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

    def test_source_search_sort(self, old_provider, new_provider):
        """Set source, search, then sort."""
        old_provider.set_sources([["readable"]])
        old_provider.set_search("test", "and")
        old_provider.set_sort(["-file_size"])

        new_provider.set_sources([["readable"]])
        new_provider.set_search("test", "and")
        new_provider.set_sort(["-file_size"])

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids

    def test_grouping_then_search(self, old_provider, new_provider):
        """Group by field, then search within groups."""
        old_provider.set_groups("extension", is_property=False, allow_singletons=True)
        old_provider.set_search("test", "and")

        new_provider.set_groups("extension", is_property=False, allow_singletons=True)
        new_provider.set_search("test", "and")

        old_ids = get_view_ids_set(old_provider)
        new_ids = get_view_ids_set(new_provider)
        assert old_ids == new_ids

    def test_full_pipeline(self, old_provider, new_provider):
        """Test full pipeline: source -> grouping -> group -> search -> sort."""
        old_provider.set_sources([["readable"]])
        old_provider.set_groups("extension", is_property=False, allow_singletons=True)
        old_provider.set_group(0)
        old_provider.set_search("test", "and")
        old_provider.set_sort(["title"])

        new_provider.set_sources([["readable"]])
        new_provider.set_groups("extension", is_property=False, allow_singletons=True)
        new_provider.set_group(0)
        new_provider.set_search("test", "and")
        new_provider.set_sort(["title"])

        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids


# =============================================================================
# get_current_state tests
# =============================================================================


class TestProviderGetCurrentState:
    """Tests for provider.get_current_state() behavior."""

    def test_get_current_state_basic(self, old_provider, new_provider):
        """get_current_state returns consistent results."""
        old_state = old_provider.get_current_state(page_size=10, page_number=0)
        new_state = new_provider.get_current_state(page_size=10, page_number=0)

        assert old_state.view_count == new_state.view_count
        assert old_state.selection_count == new_state.selection_count
        assert old_state.nb_pages == new_state.nb_pages
        assert old_state.source_count == new_state.source_count

    def test_get_current_state_videos(self, old_provider, new_provider):
        """get_current_state returns same video IDs."""
        old_state = old_provider.get_current_state(page_size=20, page_number=0)
        new_state = new_provider.get_current_state(page_size=20, page_number=0)

        old_video_ids = [v.video_id for v in old_state.result]
        new_video_ids = [v.video_id for v in new_state.result]
        assert old_video_ids == new_video_ids

    def test_get_current_state_pagination(self, old_provider, new_provider):
        """get_current_state pagination works consistently."""
        # Page 0
        old_p0 = old_provider.get_current_state(page_size=50, page_number=0)
        new_p0 = new_provider.get_current_state(page_size=50, page_number=0)
        assert [v.video_id for v in old_p0.result] == [
            v.video_id for v in new_p0.result
        ]

        # Page 1
        old_p1 = old_provider.get_current_state(page_size=50, page_number=1)
        new_p1 = new_provider.get_current_state(page_size=50, page_number=1)
        assert [v.video_id for v in old_p1.result] == [
            v.video_id for v in new_p1.result
        ]

        # Different pages have different videos
        assert [v.video_id for v in old_p0.result] != [
            v.video_id for v in old_p1.result
        ]

    def test_get_current_state_with_search(self, old_provider, new_provider):
        """get_current_state with search filter."""
        old_provider.set_search("action", "and")
        new_provider.set_search("action", "and")

        old_state = old_provider.get_current_state(page_size=100, page_number=0)
        new_state = new_provider.get_current_state(page_size=100, page_number=0)

        assert old_state.view_count == new_state.view_count
        assert old_state.selection_count == new_state.selection_count
        old_video_ids = [v.video_id for v in old_state.result]
        new_video_ids = [v.video_id for v in new_state.result]
        assert old_video_ids == new_video_ids

    def test_get_current_state_with_sort(self, old_provider, new_provider):
        """get_current_state with custom sort."""
        old_provider.set_sort(["-file_size"])
        new_provider.set_sort(["-file_size"])

        old_state = old_provider.get_current_state(page_size=20, page_number=0)
        new_state = new_provider.get_current_state(page_size=20, page_number=0)

        old_video_ids = [v.video_id for v in old_state.result]
        new_video_ids = [v.video_id for v in new_state.result]
        assert old_video_ids == new_video_ids

        # Verify sort order (file sizes should be descending)
        old_sizes = [v.file_size for v in old_state.result]
        new_sizes = [v.file_size for v in new_state.result]
        assert old_sizes == new_sizes
        assert old_sizes == sorted(old_sizes, reverse=True)


# =============================================================================
# Video attribute consistency tests (via get_current_state)
# =============================================================================


class TestVideoAttributes:
    """Tests ensuring video attributes are consistent between databases."""

    def test_video_basic_attributes(self, old_provider, new_provider):
        """Basic video attributes match."""
        old_state = old_provider.get_current_state(page_size=100, page_number=0)
        new_state = new_provider.get_current_state(page_size=100, page_number=0)

        for old_v, new_v in zip(old_state.result, new_state.result):
            assert old_v.video_id == new_v.video_id
            assert str(old_v.filename) == str(new_v.filename)
            assert old_v.file_size == new_v.file_size
            assert str(old_v.title) == str(new_v.title)
            assert old_v.extension == new_v.extension

    def test_video_technical_attributes(self, old_provider, new_provider):
        """Technical video attributes match."""
        old_state = old_provider.get_current_state(page_size=100, page_number=0)
        new_state = new_provider.get_current_state(page_size=100, page_number=0)

        for old_v, new_v in zip(old_state.result, new_state.result):
            assert old_v.duration == new_v.duration
            assert old_v.width == new_v.width
            assert old_v.height == new_v.height
            assert str(old_v.video_codec) == str(new_v.video_codec)
            assert str(old_v.audio_codec) == str(new_v.audio_codec)
            assert str(old_v.container_format) == str(new_v.container_format)

    def test_video_flags(self, old_provider, new_provider):
        """Video flags match."""
        old_state = old_provider.get_current_state(page_size=100, page_number=0)
        new_state = new_provider.get_current_state(page_size=100, page_number=0)

        for old_v, new_v in zip(old_state.result, new_state.result):
            assert old_v.readable == new_v.readable
            assert old_v.unreadable == new_v.unreadable
            assert old_v.found == new_v.found
            assert old_v.not_found == new_v.not_found
            assert old_v.with_thumbnails == new_v.with_thumbnails
            assert old_v.without_thumbnails == new_v.without_thumbnails

    def test_video_properties(self, old_provider, new_provider):
        """Video properties dict matches."""
        old_state = old_provider.get_current_state(page_size=100, page_number=0)
        new_state = new_provider.get_current_state(page_size=100, page_number=0)

        for old_v, new_v in zip(old_state.result, new_state.result):
            assert old_v.properties == new_v.properties

    def test_video_similarity_id(self, old_provider, new_provider):
        """Video similarity_id matches."""
        old_state = old_provider.get_current_state(page_size=100, page_number=0)
        new_state = new_provider.get_current_state(page_size=100, page_number=0)

        for old_v, new_v in zip(old_state.result, new_state.result):
            assert old_v.similarity_id == new_v.similarity_id


# =============================================================================
# Provider reset and state tests
# =============================================================================


class TestProviderState:
    """Tests for provider state management."""

    def test_reset(self, old_provider, new_provider):
        """reset() should restore default state."""
        # Modify state
        old_provider.set_search("test", "and")
        old_provider.set_sort(["-file_size"])
        new_provider.set_search("test", "and")
        new_provider.set_sort(["-file_size"])

        # Reset
        old_provider.reset()
        new_provider.reset()

        # Should be back to defaults
        old_ids = get_view_ids(old_provider)
        new_ids = get_view_ids(new_provider)
        assert old_ids == new_ids

    def test_get_sources(self, old_provider, new_provider):
        """get_sources() returns current sources."""
        old_provider.set_sources([["readable", "found"]])
        new_provider.set_sources([["readable", "found"]])

        assert old_provider.get_sources() == new_provider.get_sources()

    def test_get_search(self, old_provider, new_provider):
        """get_search() returns current search."""
        old_provider.set_search("test query", "or")
        new_provider.set_search("test query", "or")

        old_search = old_provider.get_search()
        new_search = new_provider.get_search()
        assert old_search.text == new_search.text
        assert old_search.cond == new_search.cond

    def test_get_sort(self, old_provider, new_provider):
        """get_sort() returns current sort."""
        old_provider.set_sort(["-width", "height"])
        new_provider.set_sort(["-width", "height"])

        assert old_provider.get_sort() == new_provider.get_sort()

    def test_get_grouping(self, old_provider, new_provider):
        """get_grouping() returns current grouping."""
        old_provider.set_groups("extension", is_property=False, allow_singletons=True)
        new_provider.set_groups("extension", is_property=False, allow_singletons=True)

        old_grouping = old_provider.get_grouping()
        new_grouping = new_provider.get_grouping()
        assert old_grouping.field == new_grouping.field
        assert old_grouping.is_property == new_grouping.is_property
        assert old_grouping.allow_singletons == new_grouping.allow_singletons


# =============================================================================
# Classifier layer tests (requires in-memory databases with test properties)
# =============================================================================


@pytest.fixture
def old_provider_with_categories(mem_old_database):
    """
    Provider with a 'category' multi-value property for classifier tests.

    The 'category' property is pre-populated in the test databases via
    tests/setup_category_property.py. Videos have categories based on folder:
    - Videos in 'action' folder: categories [action, thriller]
    - Videos in 'comedy' folder: categories [comedy, romance]
    - Videos in 'drama' folder: categories [drama, thriller]
    - Videos in 'documentary' folder: categories [documentary]
    - etc.

    This allows testing classifier paths like [thriller] which would group
    action and drama videos together, then sub-classify by their other values.
    """
    provider = mem_old_database.provider
    provider.reset()
    return provider


@pytest.fixture
def new_provider_with_categories(mem_new_database):
    """Same as old_provider_with_categories but for NewSQL database."""
    provider = mem_new_database.provider
    provider.reset()
    return provider


class TestProviderClassifier:
    """Tests for provider.set_classifier_path() behavior."""

    def test_classifier_empty_path(
        self, old_provider_with_categories, new_provider_with_categories
    ):
        """Empty classifier path should return same groups as grouping layer."""
        old_p = old_provider_with_categories
        new_p = new_provider_with_categories

        # Group by the multi-value property
        old_p.set_groups("category", is_property=True, allow_singletons=True)
        new_p.set_groups("category", is_property=True, allow_singletons=True)

        # Empty classifier path
        old_p.set_classifier_path([])
        new_p.set_classifier_path([])

        old_p.get_view_indices()
        new_p.get_view_indices()

        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()

        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {s.value: s.count for s in new_stats}
        assert old_groups == new_groups

    def test_classifier_single_value_path(
        self, old_provider_with_categories, new_provider_with_categories
    ):
        """Classifier with single value filters to videos with that value."""
        old_p = old_provider_with_categories
        new_p = new_provider_with_categories

        old_p.set_groups("category", is_property=True, allow_singletons=True)
        new_p.set_groups("category", is_property=True, allow_singletons=True)

        # Set classifier path to ["thriller"]
        # This should filter to videos that have "thriller" category
        old_p.set_classifier_path(["thriller"])
        new_p.set_classifier_path(["thriller"])

        old_ids = get_view_ids_set(old_p)
        new_ids = get_view_ids_set(new_p)
        assert old_ids == new_ids
        assert len(old_ids) > 0  # Should have some videos

    def test_classifier_shows_remaining_values(
        self, old_provider_with_categories, new_provider_with_categories
    ):
        """Classifier should show groups for other values of the same property."""
        old_p = old_provider_with_categories
        new_p = new_provider_with_categories

        old_p.set_groups("category", is_property=True, allow_singletons=True)
        new_p.set_groups("category", is_property=True, allow_singletons=True)

        # Set classifier path to ["thriller"]
        old_p.set_classifier_path(["thriller"])
        new_p.set_classifier_path(["thriller"])

        old_p.get_view_indices()
        new_p.get_view_indices()

        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()

        # Get group values (should not include "thriller" since it's in the path)
        old_values = {s.value for s in old_stats if s.value is not None}
        new_values = {s.value for s in new_stats if s.value is not None}

        assert old_values == new_values
        assert "thriller" not in old_values  # Path value should be excluded

        # Should include other values like "action" and "drama"
        # (videos that have thriller also have action or drama)
        assert "action" in old_values or "drama" in old_values

    def test_classifier_multi_value_path(
        self, old_provider_with_categories, new_provider_with_categories
    ):
        """Classifier with multiple values filters to intersection."""
        old_p = old_provider_with_categories
        new_p = new_provider_with_categories

        old_p.set_groups("category", is_property=True, allow_singletons=True)
        new_p.set_groups("category", is_property=True, allow_singletons=True)

        # First get videos with just "thriller"
        old_p.set_classifier_path(["thriller"])
        new_p.set_classifier_path(["thriller"])
        thriller_old = get_view_ids_set(old_p)
        thriller_new = get_view_ids_set(new_p)

        # Now add "action" to path - should be intersection
        old_p.set_classifier_path(["thriller", "action"])
        new_p.set_classifier_path(["thriller", "action"])

        thriller_action_old = get_view_ids_set(old_p)
        thriller_action_new = get_view_ids_set(new_p)

        assert thriller_action_old == thriller_action_new
        # Intersection should be subset of single filter
        assert thriller_action_old.issubset(thriller_old)
        assert thriller_action_new.issubset(thriller_new)

    def test_classifier_get_path(
        self, old_provider_with_categories, new_provider_with_categories
    ):
        """get_classifier_path() returns current path."""
        old_p = old_provider_with_categories
        new_p = new_provider_with_categories

        old_p.set_groups("category", is_property=True, allow_singletons=True)
        new_p.set_groups("category", is_property=True, allow_singletons=True)

        old_p.set_classifier_path(["thriller", "action"])
        new_p.set_classifier_path(["thriller", "action"])

        assert old_p.get_classifier_path() == ["thriller", "action"]
        assert new_p.get_classifier_path() == ["thriller", "action"]
        assert old_p.get_classifier_path() == new_p.get_classifier_path()

    def test_classifier_select_group(
        self, old_provider_with_categories, new_provider_with_categories
    ):
        """classifier_select_group() adds value to path."""
        old_p = old_provider_with_categories
        new_p = new_provider_with_categories

        old_p.set_groups("category", is_property=True, allow_singletons=True)
        new_p.set_groups("category", is_property=True, allow_singletons=True)

        # Start with empty path
        old_p.set_classifier_path([])
        new_p.set_classifier_path([])

        # Get view to compute groups
        old_p.get_view_indices()
        new_p.get_view_indices()

        # Find the group ID for "thriller"
        old_stats = old_p.get_classifier_stats()
        thriller_group_id = None
        for i, stat in enumerate(old_stats):
            if stat.value == "thriller":
                thriller_group_id = i
                break

        if thriller_group_id is not None:
            old_p.classifier_select_group(thriller_group_id)
            new_p.classifier_select_group(thriller_group_id)

            # Path should now include "thriller"
            assert old_p.get_classifier_path() == ["thriller"]
            assert new_p.get_classifier_path() == ["thriller"]

            # Videos should be filtered
            old_ids = get_view_ids_set(old_p)
            new_ids = get_view_ids_set(new_p)
            assert old_ids == new_ids

    def test_classifier_back(
        self, old_provider_with_categories, new_provider_with_categories
    ):
        """classifier_back() removes last value from path."""
        old_p = old_provider_with_categories
        new_p = new_provider_with_categories

        old_p.set_groups("category", is_property=True, allow_singletons=True)
        new_p.set_groups("category", is_property=True, allow_singletons=True)

        # Set a path with multiple values
        old_p.set_classifier_path(["thriller", "action"])
        new_p.set_classifier_path(["thriller", "action"])

        # Go back
        old_p.classifier_back()
        new_p.classifier_back()

        assert old_p.get_classifier_path() == ["thriller"]
        assert new_p.get_classifier_path() == ["thriller"]

        # Go back again
        old_p.classifier_back()
        new_p.classifier_back()

        assert old_p.get_classifier_path() == []
        assert new_p.get_classifier_path() == []

    def test_classifier_only_works_with_multi_property(
        self, old_provider_with_categories, new_provider_with_categories
    ):
        """Classifier only works when grouping by multi-value property."""
        old_p = old_provider_with_categories
        new_p = new_provider_with_categories

        # Group by a non-property field (extension)
        old_p.set_groups("extension", is_property=False, allow_singletons=True)
        new_p.set_groups("extension", is_property=False, allow_singletons=True)

        # Setting classifier path should have no effect
        old_p.set_classifier_path(["mp4"])
        new_p.set_classifier_path(["mp4"])

        # Get view - classifier should pass through without filtering
        old_ids = get_view_ids_set(old_p)
        new_ids = get_view_ids_set(new_p)
        assert old_ids == new_ids

    def test_classifier_group_selection_after_path(
        self, old_provider_with_categories, new_provider_with_categories
    ):
        """Can select a group after setting classifier path."""
        old_p = old_provider_with_categories
        new_p = new_provider_with_categories

        old_p.set_groups("category", is_property=True, allow_singletons=True)
        new_p.set_groups("category", is_property=True, allow_singletons=True)

        # Set classifier path
        old_p.set_classifier_path(["thriller"])
        new_p.set_classifier_path(["thriller"])

        old_p.get_view_indices()
        new_p.get_view_indices()

        # Get stats to find groups
        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()

        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {s.value: s.count for s in new_stats}
        assert old_groups == new_groups

        # Select a specific group (group 0 is usually None = all videos in path)
        if len(old_stats) > 1:
            old_p.set_group(1)
            new_p.set_group(1)

            old_ids = get_view_ids_set(old_p)
            new_ids = get_view_ids_set(new_p)
            assert old_ids == new_ids

    def test_classifier_reverse(
        self, old_provider_with_categories, new_provider_with_categories
    ):
        """classifier_reverse() reverses the path order."""
        old_p = old_provider_with_categories
        new_p = new_provider_with_categories

        old_p.set_groups("category", is_property=True, allow_singletons=True)
        new_p.set_groups("category", is_property=True, allow_singletons=True)

        old_p.set_classifier_path(["thriller", "action"])
        new_p.set_classifier_path(["thriller", "action"])

        old_reversed = old_p.classifier_reverse()
        new_reversed = new_p.classifier_reverse()

        assert old_reversed == ["action", "thriller"]
        assert new_reversed == ["action", "thriller"]
        assert old_p.get_classifier_path() == ["action", "thriller"]
        assert new_p.get_classifier_path() == ["action", "thriller"]

    def test_classifier_videos_have_all_path_values(
        self, old_provider_with_categories, new_provider_with_categories
    ):
        """Videos returned by classifier should have ALL values in the path."""
        old_p = old_provider_with_categories
        new_p = new_provider_with_categories

        old_p.set_groups("category", is_property=True, allow_singletons=True)
        new_p.set_groups("category", is_property=True, allow_singletons=True)

        # Set classifier path to ["thriller"]
        old_p.set_classifier_path(["thriller"])
        new_p.set_classifier_path(["thriller"])

        # Get resulting videos
        old_state = old_p.get_current_state(page_size=1000, page_number=0)
        new_state = new_p.get_current_state(page_size=1000, page_number=0)

        # All videos should have "thriller" in their categories
        for video in old_state.result:
            categories = video.properties.get("category", [])
            assert "thriller" in categories, (
                f"Video {video.video_id} missing 'thriller'"
            )

        for video in new_state.result:
            categories = video.properties.get("category", [])
            assert "thriller" in categories, (
                f"Video {video.video_id} missing 'thriller'"
            )

    def test_classifier_excluded_values_not_in_groups(
        self, old_provider_with_categories, new_provider_with_categories
    ):
        """Values in the classifier path should not appear in group stats."""
        old_p = old_provider_with_categories
        new_p = new_provider_with_categories

        old_p.set_groups("category", is_property=True, allow_singletons=True)
        new_p.set_groups("category", is_property=True, allow_singletons=True)

        # Set a path
        old_p.set_classifier_path(["thriller", "action"])
        new_p.set_classifier_path(["thriller", "action"])

        old_p.get_view_indices()
        new_p.get_view_indices()

        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()

        # Path values should not be in the groups
        old_values = {s.value for s in old_stats}
        new_values = {s.value for s in new_stats}

        assert "thriller" not in old_values
        assert "action" not in old_values
        assert "thriller" not in new_values
        assert "action" not in new_values
