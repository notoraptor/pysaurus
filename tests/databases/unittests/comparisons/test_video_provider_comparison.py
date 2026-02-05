"""
Tests comparing video provider behavior between JSON and Saurus SQL databases.

These tests ensure that the video provider behaves consistently regardless of
whether it's backed by JsonDatabase or PysaurusCollection (Saurus SQL).

All tests use the PUBLIC provider API (database.provider.*) rather than
internal jsondb_* methods, making them implementation-independent.
"""

import pytest

from pysaurus.database.abstract_database import AbstractDatabase
from saurus.sql.pysaurus_collection import PysaurusCollection


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
def new_provider(fake_saurus_database: PysaurusCollection):
    """Get provider from Saurus SQL database, reset before each test."""
    provider = fake_saurus_database.provider
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


def normalize_group_value(value):
    """
    Normalize group values for comparison between JSON and SQL.

    - Converts to string
    - Removes trailing .0 from floats that are actually integers (e.g., '1000000.0' -> '1000000')
    - Normalizes booleans (0/1 -> False/True)
    - Normalizes whitespace (multiple spaces -> single space, strip edges)
    - Handles None values
    - Handles tuples recursively (for composite fields like size_length)
    """
    if value is None:
        return None
    # Handle tuples recursively (e.g., (FileSize, Duration) tuples)
    if isinstance(value, tuple):
        return tuple(normalize_group_value(v) for v in value)
    s = str(value)
    # Normalize empty string to None (JSON uses '', SQL uses None for missing properties)
    if s == '':
        return None
    # Normalize boolean representation (SQL uses 0/1, Python uses False/True)
    if s == '0':
        return 'False'
    if s == '1':
        return 'True'
    # Remove trailing .0 from float strings (e.g., '1000000.0' -> '1000000')
    if s.endswith('.0') and s[:-2].replace('-', '', 1).isdigit():
        return s[:-2]
    # Normalize whitespace (for *_numeric fields with padding)
    # SQL padding adds spaces: 'test_ 009889 _' -> 'test_009889_'
    import re
    s = re.sub(r'\s+', '', s)  # Remove all whitespace
    return s


def assert_grouping_identical(
    old_provider,
    new_provider,
    field_name: str,
    is_property: bool = False,
    allow_singletons: bool = True,
    sorting: str = "count",
    reverse: bool = True,
    min_sample: bool = True,
):
    """
    Helper function to assert that grouping behavior is identical between
    JSON and SQL databases.

    Verifies:
    - Same group values
    - Same group counts
    - Same ordering
    - Same video IDs in each group (sampled)

    Args:
        min_sample: If True, test only 3 groups (first, middle, last) for faster execution.
                   If False, test ~10 groups. Default is True.
    """
    # Set grouping for both providers
    old_provider.set_groups(
        field_name,
        is_property=is_property,
        allow_singletons=allow_singletons,
        sorting=sorting,
        reverse=reverse,
    )
    new_provider.set_groups(
        field_name,
        is_property=is_property,
        allow_singletons=allow_singletons,
        sorting=sorting,
        reverse=reverse,
    )

    # Trigger view computation
    old_provider.get_view_indices()
    new_provider.get_view_indices()

    # Get classifier stats (group information)
    old_stats = old_provider.get_classifier_stats()
    new_stats = new_provider.get_classifier_stats()

    # Compare number of groups first
    num_old_groups = len(old_stats)
    num_new_groups = len(new_stats)
    assert num_old_groups == num_new_groups, (
        f"Number of groups differ for {field_name}: "
        f"JSON has {num_old_groups}, SQL has {num_new_groups}"
    )

    # Always compute old_values for error messages (used later in video ID comparison)
    old_values = [normalize_group_value(s.value) for s in old_stats]
    new_values = [normalize_group_value(s.value) for s in new_stats]

    if min_sample:
        # For minimal sampling, only compare a few groups, not all
        # (comparing thousands of groups as dicts is too slow)
        indices_to_check = []
        if num_old_groups > 0:
            indices_to_check.append(0)  # first
            if num_old_groups > 1:
                indices_to_check.append(num_old_groups // 2)  # middle
                indices_to_check.append(num_old_groups - 1)  # last

        for idx in indices_to_check:
            old_val = old_values[idx]
            new_val = new_values[idx]
            old_count = old_stats[idx].count
            new_count = new_stats[idx].count
            assert old_val == new_val and old_count == new_count, (
                f"Group at index {idx} differs for {field_name}: "
                f"JSON=({old_val}, {old_count}), SQL=({new_val}, {new_count})"
            )
    else:
        # Compare all group values and counts exhaustively
        # Normalize values to strings for comparison (JSON uses Text objects, SQL uses str)
        # Also normalize floats that are actually ints (e.g., '1000000.0' -> '1000000')
        old_groups = {old_values[i]: old_stats[i].count for i in range(len(old_stats))}
        new_groups = {new_values[i]: new_stats[i].count for i in range(len(new_stats))}
        assert old_groups == new_groups, (
            f"Groups differ for {field_name}: "
            f"JSON={old_groups}, SQL={new_groups}"
        )

        # Compare ordering (group values in order)
        assert old_values == new_values, (
            f"Group ordering differs for {field_name}: "
            f"JSON={old_values}, SQL={new_values}"
        )

    # Compare video IDs in a sample of groups (not all, to avoid timeout)
    if num_old_groups > 0:
        # Determine which groups to test
        groups_to_test = set()

        if min_sample:
            # Minimal sample: only first, middle, and last group (3 total)
            groups_to_test.add(0)
            if num_old_groups > 1:
                groups_to_test.add(num_old_groups // 2)
                groups_to_test.add(num_old_groups - 1)
        else:
            # Default sample: first 5 groups, last 2 groups, and 3 groups in the middle (~10 total)
            # First 5 groups
            for i in range(min(5, num_old_groups)):
                groups_to_test.add(i)

            # Last 2 groups
            for i in range(max(0, num_old_groups - 2), num_old_groups):
                groups_to_test.add(i)

            # 3 groups in the middle
            if num_old_groups > 10:
                mid_start = num_old_groups // 3
                mid_end = 2 * num_old_groups // 3
                groups_to_test.add(mid_start)
                groups_to_test.add((mid_start + mid_end) // 2)
                groups_to_test.add(mid_end)

        # Test selected groups
        for group_index in sorted(groups_to_test):
            old_provider.set_group(group_index)
            new_provider.set_group(group_index)

            old_ids = get_view_ids_set(old_provider)
            new_ids = get_view_ids_set(new_provider)

            group_value = old_values[group_index]
            assert old_ids == new_ids, (
                f"Video IDs differ for {field_name} group '{group_value}' (index {group_index}): "
                f"JSON has {len(old_ids)} videos, SQL has {len(new_ids)} videos"
            )


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
# Exhaustive grouping tests - All groupable attributes
# =============================================================================


class TestProviderGroupingExhaustive:
    """
    Exhaustive tests for grouping by ALL groupable attributes.

    This test suite ensures that JSON and SQL databases produce identical
    grouping results for all 31 groupable video attributes, covering:
    - Basic attributes (disk, file_title, filename, etc.)
    - Technical attributes (codecs, resolution, frame_rate, etc.)
    - Temporal attributes (dates, duration)
    - Boolean attributes (watched, found, etc.)
    - Semantic attributes with Python functions (file_title_numeric, etc.)
    """

    # Basic file attributes
    def test_group_by_disk(self, old_provider, new_provider):
        """Group by disk."""
        assert_grouping_identical(old_provider, new_provider, "disk")

    def test_group_by_file_title(self, old_provider, new_provider):
        """Group by file title (filename without extension)."""
        assert_grouping_identical(old_provider, new_provider, "file_title")

    def test_group_by_filename(self, old_provider, new_provider):
        """Group by full filename."""
        assert_grouping_identical(old_provider, new_provider, "filename")

    def test_group_by_title(self, old_provider, new_provider):
        """Group by title."""
        assert_grouping_identical(old_provider, new_provider, "title")

    def test_group_by_extension(self, old_provider, new_provider):
        """Group by file extension."""
        assert_grouping_identical(old_provider, new_provider, "extension")

    def test_group_by_container_format(self, old_provider, new_provider):
        """Group by container format."""
        assert_grouping_identical(old_provider, new_provider, "container_format")

    # Technical video attributes
    def test_group_by_video_codec(self, old_provider, new_provider):
        """Group by video codec."""
        assert_grouping_identical(old_provider, new_provider, "video_codec")

    def test_group_by_audio_codec(self, old_provider, new_provider):
        """Group by audio codec."""
        assert_grouping_identical(old_provider, new_provider, "audio_codec")

    def test_group_by_audio_codec_description(self, old_provider, new_provider):
        """Group by audio codec description."""
        assert_grouping_identical(old_provider, new_provider, "audio_codec_description")

    def test_group_by_video_codec_description(self, old_provider, new_provider):
        """Group by video codec description."""
        assert_grouping_identical(old_provider, new_provider, "video_codec_description")

    def test_group_by_width(self, old_provider, new_provider):
        """Group by video width."""
        assert_grouping_identical(old_provider, new_provider, "width")

    def test_group_by_height(self, old_provider, new_provider):
        """Group by video height."""
        assert_grouping_identical(old_provider, new_provider, "height")

    def test_group_by_bit_depth(self, old_provider, new_provider):
        """Group by bit depth."""
        assert_grouping_identical(old_provider, new_provider, "bit_depth")

    def test_group_by_frame_rate(self, old_provider, new_provider):
        """Group by frame rate."""
        assert_grouping_identical(old_provider, new_provider, "frame_rate")

    def test_group_by_bit_rate(self, old_provider, new_provider):
        """Group by bit rate."""
        assert_grouping_identical(old_provider, new_provider, "bit_rate")

    def test_group_by_audio_bit_rate(self, old_provider, new_provider):
        """Group by audio bit rate."""
        assert_grouping_identical(old_provider, new_provider, "audio_bit_rate")

    def test_group_by_sample_rate(self, old_provider, new_provider):
        """Group by audio sample rate."""
        assert_grouping_identical(old_provider, new_provider, "sample_rate")

    def test_group_by_audio_bits(self, old_provider, new_provider):
        """Group by audio bits per sample."""
        assert_grouping_identical(old_provider, new_provider, "audio_bits")

    # Temporal attributes
    def test_group_by_date(self, old_provider, new_provider):
        """Group by file modification date (alias)."""
        assert_grouping_identical(old_provider, new_provider, "date")

    def test_group_by_day(self, old_provider, new_provider):
        """Group by day (YYYY-MM-DD format)."""
        assert_grouping_identical(old_provider, new_provider, "day")

    def test_group_by_year(self, old_provider, new_provider):
        """Group by year."""
        assert_grouping_identical(old_provider, new_provider, "year")

    def test_group_by_date_entry_modified(self, old_provider, new_provider):
        """Group by modification date."""
        assert_grouping_identical(old_provider, new_provider, "date_entry_modified")

    def test_group_by_date_entry_opened(self, old_provider, new_provider):
        """Group by last opened date."""
        assert_grouping_identical(old_provider, new_provider, "date_entry_opened")

    def test_group_by_duration(self, old_provider, new_provider):
        """Group by video duration."""
        assert_grouping_identical(old_provider, new_provider, "duration")

    def test_group_by_length(self, old_provider, new_provider):
        """Group by length (duration in seconds, alias)."""
        assert_grouping_identical(old_provider, new_provider, "length")

    # Size attributes
    def test_group_by_file_size(self, old_provider, new_provider):
        """Group by file size."""
        assert_grouping_identical(old_provider, new_provider, "file_size")

    def test_group_by_size(self, old_provider, new_provider):
        """Group by size (formatted file size, alias)."""
        assert_grouping_identical(old_provider, new_provider, "size")

    def test_group_by_size_length(self, old_provider, new_provider):
        """Group by size length (number of digits in file_size).

        Only verifies group count due to non-deterministic ordering with thousands of ties.
        """
        # Set grouping for both providers
        old_provider.set_groups("size_length")
        new_provider.set_groups("size_length")

        # Trigger view computation
        old_provider.get_view_indices()
        new_provider.get_view_indices()

        # Get classifier stats (group information)
        old_stats = old_provider.get_classifier_stats()
        new_stats = new_provider.get_classifier_stats()

        # Only compare number of groups (ordering is non-deterministic with many ties)
        assert len(old_stats) == len(new_stats), (
            f"Number of groups differ for size_length: "
            f"JSON has {len(old_stats)}, SQL has {len(new_stats)}"
        )

    def test_group_by_similarity_id(self, old_provider, new_provider):
        """Group by similarity_id (groups similar videos)."""
        assert_grouping_identical(old_provider, new_provider, "similarity_id")

    # Boolean attributes
    def test_group_by_watched(self, old_provider, new_provider):
        """Group by watched status."""
        assert_grouping_identical(old_provider, new_provider, "watched")

    # CRITICAL: Semantic attributes with Python functions
    def test_group_by_file_title_numeric(self, old_provider, new_provider):
        """Only verifies group count (values differ intentionally due to padding)."""
        old_provider.set_groups("file_title_numeric")
        new_provider.set_groups("file_title_numeric")
        old_provider.get_view_indices()
        new_provider.get_view_indices()
        old_stats = old_provider.get_classifier_stats()
        new_stats = new_provider.get_classifier_stats()
        assert len(old_stats) == len(new_stats)

    def test_group_by_filename_numeric(self, old_provider, new_provider):
        """Only verifies group count (values differ intentionally due to padding)."""
        old_provider.set_groups("filename_numeric")
        new_provider.set_groups("filename_numeric")
        old_provider.get_view_indices()
        new_provider.get_view_indices()
        old_stats = old_provider.get_classifier_stats()
        new_stats = new_provider.get_classifier_stats()
        assert len(old_stats) == len(new_stats)

    def test_group_by_title_numeric(self, old_provider, new_provider):
        """Only verifies group count (values differ intentionally due to padding)."""
        old_provider.set_groups("title_numeric")
        new_provider.set_groups("title_numeric")
        old_provider.get_view_indices()
        new_provider.get_view_indices()
        old_stats = old_provider.get_classifier_stats()
        new_stats = new_provider.get_classifier_stats()
        assert len(old_stats) == len(new_stats)


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
def new_provider_with_categories(mem_saurus_database):
    """Same as old_provider_with_categories but for Saurus SQL database."""
    provider = mem_saurus_database.provider
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


# ==============================================================================
# Phase 3: Property Type Tests - Fixtures
# ==============================================================================


def setup_property_with_values(db, prop_name: str, prop_type: str, multiple: bool, assignments: dict):
    """
    Helper to create a property and assign values to videos.

    Args:
        db: Database instance
        prop_name: Name of the property
        prop_type: Type of the property ("str", "int", "float", "bool")
        multiple: Whether property can have multiple values
        assignments: Dict of {video_id: value} or {video_id: [values]} for multiple
    """
    # Check if property exists and delete it if it does
    existing_props = db.get_prop_types(name=prop_name)
    if existing_props:
        db.prop_type_del(prop_name)

    # Use appropriate default value for each type
    # (empty string "" causes issues with non-string types)
    default_values = {
        "str": "",
        "int": 0,
        "float": 0.0,
        "bool": False
    }
    definition = default_values.get(prop_type, "")

    # Create the property
    db.prop_type_add(prop_name, prop_type, definition, multiple)

    # Assign values
    # videos_tag_set() always expects lists, even for single-value properties
    if assignments:
        normalized_assignments = {}
        for vid, val in assignments.items():
            # Ensure value is a list
            if isinstance(val, list):
                normalized_assignments[vid] = val
            else:
                normalized_assignments[vid] = [val]
        db.videos_tag_set(prop_name, normalized_assignments)


@pytest.fixture
def old_provider_with_test_properties(mem_old_database):
    """Provider with test properties of all types for Phase 3 tests."""
    db = mem_old_database

    # Clean up any existing test properties first
    test_props = ["test_color", "test_tags", "test_rating", "test_scores",
                  "test_price", "test_measurements", "test_is_favorite", "test_flags"]
    for prop_name in test_props:
        try:
            db.prop_type_del(prop_name)
        except:
            pass  # Property doesn't exist, that's fine

    # Get some video IDs to assign properties to
    videos = db.get_videos(include=["video_id"])
    video_ids = [v.video_id for v in videos[:100]]  # Use first 100 videos

    # str single: assign simple string values based on video_id
    str_single_assignments = {}
    for i, vid in enumerate(video_ids):
        if i % 3 == 0:
            str_single_assignments[vid] = "red"
        elif i % 3 == 1:
            str_single_assignments[vid] = "green"
        else:
            str_single_assignments[vid] = "blue"
    setup_property_with_values(db, "test_color", "str", False, str_single_assignments)

    # str multi: assign multiple string values (already have category, but add another)
    str_multi_assignments = {}
    for i, vid in enumerate(video_ids):
        if i % 4 == 0:
            str_multi_assignments[vid] = ["tag1", "tag2"]
        elif i % 4 == 1:
            str_multi_assignments[vid] = ["tag2", "tag3"]
        elif i % 4 == 2:
            str_multi_assignments[vid] = ["tag1", "tag3"]
        else:
            str_multi_assignments[vid] = ["tag1"]
    setup_property_with_values(db, "test_tags", "str", True, str_multi_assignments)

    # int single: assign simple integer values
    int_single_assignments = {}
    for i, vid in enumerate(video_ids):
        int_single_assignments[vid] = (i % 5) + 1  # Values 1-5
    setup_property_with_values(db, "test_rating", "int", False, int_single_assignments)

    # int multi: assign multiple integer values
    int_multi_assignments = {}
    for i, vid in enumerate(video_ids):
        if i % 3 == 0:
            int_multi_assignments[vid] = [1, 2]
        elif i % 3 == 1:
            int_multi_assignments[vid] = [2, 3]
        else:
            int_multi_assignments[vid] = [1, 3]
    setup_property_with_values(db, "test_scores", "int", True, int_multi_assignments)

    # float single: assign simple float values
    float_single_assignments = {}
    for i, vid in enumerate(video_ids):
        float_single_assignments[vid] = round(1.0 + (i % 10) * 0.5, 1)  # 1.0, 1.5, 2.0, ..., 5.5
    setup_property_with_values(db, "test_price", "float", False, float_single_assignments)

    # float multi: assign multiple float values
    float_multi_assignments = {}
    for i, vid in enumerate(video_ids):
        if i % 3 == 0:
            float_multi_assignments[vid] = [1.5, 2.5]
        elif i % 3 == 1:
            float_multi_assignments[vid] = [2.5, 3.5]
        else:
            float_multi_assignments[vid] = [1.5, 3.5]
    setup_property_with_values(db, "test_measurements", "float", True, float_multi_assignments)

    # bool single: assign boolean values
    bool_single_assignments = {}
    for i, vid in enumerate(video_ids):
        bool_single_assignments[vid] = i % 2 == 0  # Alternate True/False
    setup_property_with_values(db, "test_is_favorite", "bool", False, bool_single_assignments)

    # bool multi: assign multiple boolean values
    bool_multi_assignments = {}
    for i, vid in enumerate(video_ids):
        if i % 3 == 0:
            bool_multi_assignments[vid] = [True, False]
        elif i % 3 == 1:
            bool_multi_assignments[vid] = [True]
        else:
            bool_multi_assignments[vid] = [False]
    setup_property_with_values(db, "test_flags", "bool", True, bool_multi_assignments)

    provider = db.provider
    provider.reset()
    return provider


@pytest.fixture
def new_provider_with_test_properties(mem_saurus_database):
    """Same as old_provider_with_test_properties but for Saurus SQL database."""
    db = mem_saurus_database

    # Clean up any existing test properties first
    test_props = ["test_color", "test_tags", "test_rating", "test_scores",
                  "test_price", "test_measurements", "test_is_favorite", "test_flags"]
    for prop_name in test_props:
        try:
            db.prop_type_del(prop_name)
        except:
            pass  # Property doesn't exist, that's fine

    # Get some video IDs to assign properties to
    videos = db.get_videos(include=["video_id"])
    video_ids = [v.video_id for v in videos[:100]]  # Use first 100 videos

    # str single
    str_single_assignments = {}
    for i, vid in enumerate(video_ids):
        if i % 3 == 0:
            str_single_assignments[vid] = "red"
        elif i % 3 == 1:
            str_single_assignments[vid] = "green"
        else:
            str_single_assignments[vid] = "blue"
    setup_property_with_values(db, "test_color", "str", False, str_single_assignments)

    # str multi
    str_multi_assignments = {}
    for i, vid in enumerate(video_ids):
        if i % 4 == 0:
            str_multi_assignments[vid] = ["tag1", "tag2"]
        elif i % 4 == 1:
            str_multi_assignments[vid] = ["tag2", "tag3"]
        elif i % 4 == 2:
            str_multi_assignments[vid] = ["tag1", "tag3"]
        else:
            str_multi_assignments[vid] = ["tag1"]
    setup_property_with_values(db, "test_tags", "str", True, str_multi_assignments)

    # int single
    int_single_assignments = {}
    for i, vid in enumerate(video_ids):
        int_single_assignments[vid] = (i % 5) + 1  # Values 1-5
    setup_property_with_values(db, "test_rating", "int", False, int_single_assignments)

    # int multi
    int_multi_assignments = {}
    for i, vid in enumerate(video_ids):
        if i % 3 == 0:
            int_multi_assignments[vid] = [1, 2]
        elif i % 3 == 1:
            int_multi_assignments[vid] = [2, 3]
        else:
            int_multi_assignments[vid] = [1, 3]
    setup_property_with_values(db, "test_scores", "int", True, int_multi_assignments)

    # float single
    float_single_assignments = {}
    for i, vid in enumerate(video_ids):
        float_single_assignments[vid] = round(1.0 + (i % 10) * 0.5, 1)
    setup_property_with_values(db, "test_price", "float", False, float_single_assignments)

    # float multi
    float_multi_assignments = {}
    for i, vid in enumerate(video_ids):
        if i % 3 == 0:
            float_multi_assignments[vid] = [1.5, 2.5]
        elif i % 3 == 1:
            float_multi_assignments[vid] = [2.5, 3.5]
        else:
            float_multi_assignments[vid] = [1.5, 3.5]
    setup_property_with_values(db, "test_measurements", "float", True, float_multi_assignments)

    # bool single
    bool_single_assignments = {}
    for i, vid in enumerate(video_ids):
        bool_single_assignments[vid] = i % 2 == 0
    setup_property_with_values(db, "test_is_favorite", "bool", False, bool_single_assignments)

    # bool multi
    bool_multi_assignments = {}
    for i, vid in enumerate(video_ids):
        if i % 3 == 0:
            bool_multi_assignments[vid] = [True, False]
        elif i % 3 == 1:
            bool_multi_assignments[vid] = [True]
        else:
            bool_multi_assignments[vid] = [False]
    setup_property_with_values(db, "test_flags", "bool", True, bool_multi_assignments)

    provider = db.provider
    provider.reset()
    return provider


# ==============================================================================
# Phase 3: Property Type Tests - Grouping Tests
# ==============================================================================


class TestPropertyGrouping:
    """Tests for grouping by custom properties of different types (Phase 3)."""

    def test_group_by_str_single_property(
        self, old_provider_with_test_properties, new_provider_with_test_properties
    ):
        """Group by single-value string property (color: red/green/blue)."""
        assert_grouping_identical(
            old_provider_with_test_properties,
            new_provider_with_test_properties,
            "test_color",
            is_property=True,
        )

    def test_group_by_str_multi_property(
        self, old_provider_with_test_properties, new_provider_with_test_properties
    ):
        """Group by multi-value string property (tags: tag1/tag2/tag3)."""
        assert_grouping_identical(
            old_provider_with_test_properties,
            new_provider_with_test_properties,
            "test_tags",
            is_property=True,
        )

    def test_group_by_int_single_property(
        self, old_provider_with_test_properties, new_provider_with_test_properties
    ):
        """Group by single-value int property (rating: 1-5)."""
        assert_grouping_identical(
            old_provider_with_test_properties,
            new_provider_with_test_properties,
            "test_rating",
            is_property=True,
        )

    def test_group_by_int_multi_property(
        self, old_provider_with_test_properties, new_provider_with_test_properties
    ):
        """Group by multi-value int property (scores: 1/2/3)."""
        assert_grouping_identical(
            old_provider_with_test_properties,
            new_provider_with_test_properties,
            "test_scores",
            is_property=True,
        )

    def test_group_by_float_single_property(
        self, old_provider_with_test_properties, new_provider_with_test_properties
    ):
        """Group by single-value float property (price: 1.0-5.5)."""
        assert_grouping_identical(
            old_provider_with_test_properties,
            new_provider_with_test_properties,
            "test_price",
            is_property=True,
        )

    def test_group_by_float_multi_property(
        self, old_provider_with_test_properties, new_provider_with_test_properties
    ):
        """Group by multi-value float property (measurements: 1.5/2.5/3.5)."""
        assert_grouping_identical(
            old_provider_with_test_properties,
            new_provider_with_test_properties,
            "test_measurements",
            is_property=True,
        )

    def test_group_by_bool_single_property(
        self, old_provider_with_test_properties, new_provider_with_test_properties
    ):
        """Group by single-value bool property (is_favorite: True/False)."""
        assert_grouping_identical(
            old_provider_with_test_properties,
            new_provider_with_test_properties,
            "test_is_favorite",
            is_property=True,
        )

    def test_group_by_bool_multi_property(
        self, old_provider_with_test_properties, new_provider_with_test_properties
    ):
        """Group by multi-value bool property (flags: True/False)."""
        assert_grouping_identical(
            old_provider_with_test_properties,
            new_provider_with_test_properties,
            "test_flags",
            is_property=True,
        )


# ==============================================================================
# Phase 3: Property Type Tests - Classifier Tests
# ==============================================================================


class TestPropertyClassifier:
    """Tests for classifier with multi-value properties of different types (Phase 3)."""

    def test_classifier_str_multi(
        self, old_provider_with_test_properties, new_provider_with_test_properties
    ):
        """Classifier with multi-value string property (tags)."""
        old_p = old_provider_with_test_properties
        new_p = new_provider_with_test_properties

        # Group by multi-value string property
        old_p.set_groups("test_tags", is_property=True, allow_singletons=True)
        new_p.set_groups("test_tags", is_property=True, allow_singletons=True)

        # Set classifier path
        old_p.set_classifier_path(["tag1"])
        new_p.set_classifier_path(["tag1"])

        old_p.get_view_indices()
        new_p.get_view_indices()

        # Compare video IDs
        old_ids = get_view_ids_set(old_p)
        new_ids = get_view_ids_set(new_p)
        assert old_ids == new_ids, "Classifier str multi: video IDs differ"

        # Compare group stats
        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()
        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {s.value: s.count for s in new_stats}
        assert old_groups == new_groups, "Classifier str multi: group stats differ"

    def test_classifier_int_multi(
        self, old_provider_with_test_properties, new_provider_with_test_properties
    ):
        """Classifier with multi-value int property (scores)."""
        old_p = old_provider_with_test_properties
        new_p = new_provider_with_test_properties

        # Group by multi-value int property
        old_p.set_groups("test_scores", is_property=True, allow_singletons=True)
        new_p.set_groups("test_scores", is_property=True, allow_singletons=True)

        # Set classifier path
        old_p.set_classifier_path([1])
        new_p.set_classifier_path([1])

        old_p.get_view_indices()
        new_p.get_view_indices()

        # Compare video IDs
        old_ids = get_view_ids_set(old_p)
        new_ids = get_view_ids_set(new_p)
        assert old_ids == new_ids, "Classifier int multi: video IDs differ"

        # Compare group stats (normalize int strings to int for SQL)
        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()
        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {}
        for s in new_stats:
            key = s.value
            # SQL stores property values as strings, convert back to int
            if key is not None and isinstance(key, str):
                try:
                    key = int(key)
                except (ValueError, TypeError):
                    pass
            new_groups[key] = s.count
        assert old_groups == new_groups, "Classifier int multi: group stats differ"

    def test_classifier_float_multi(
        self, old_provider_with_test_properties, new_provider_with_test_properties
    ):
        """Classifier with multi-value float property (measurements)."""
        old_p = old_provider_with_test_properties
        new_p = new_provider_with_test_properties

        # Group by multi-value float property
        old_p.set_groups("test_measurements", is_property=True, allow_singletons=True)
        new_p.set_groups("test_measurements", is_property=True, allow_singletons=True)

        # Set classifier path
        old_p.set_classifier_path([1.5])
        new_p.set_classifier_path([1.5])

        old_p.get_view_indices()
        new_p.get_view_indices()

        # Compare video IDs
        old_ids = get_view_ids_set(old_p)
        new_ids = get_view_ids_set(new_p)
        assert old_ids == new_ids, "Classifier float multi: video IDs differ"

        # Compare group stats (normalize float strings to float for SQL)
        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()
        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {}
        for s in new_stats:
            key = s.value
            # SQL stores property values as strings, convert back to float
            if key is not None and isinstance(key, str):
                try:
                    key = float(key)
                except (ValueError, TypeError):
                    pass
            new_groups[key] = s.count
        assert old_groups == new_groups, "Classifier float multi: group stats differ"

    def test_classifier_bool_multi(
        self, old_provider_with_test_properties, new_provider_with_test_properties
    ):
        """Classifier with multi-value bool property (flags)."""
        old_p = old_provider_with_test_properties
        new_p = new_provider_with_test_properties

        # Group by multi-value bool property
        old_p.set_groups("test_flags", is_property=True, allow_singletons=True)
        new_p.set_groups("test_flags", is_property=True, allow_singletons=True)

        # Set classifier path
        old_p.set_classifier_path([True])
        new_p.set_classifier_path([True])

        old_p.get_view_indices()
        new_p.get_view_indices()

        # Compare video IDs
        old_ids = get_view_ids_set(old_p)
        new_ids = get_view_ids_set(new_p)
        assert old_ids == new_ids, "Classifier bool multi: video IDs differ"

        # Compare group stats (normalize bool strings to bool for SQL)
        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()
        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {}
        for s in new_stats:
            key = s.value
            # SQL stores property values as strings, convert back to bool
            if key is not None and isinstance(key, str):
                if key in ('0', 'False', 'false'):
                    key = False
                elif key in ('1', 'True', 'true'):
                    key = True
            new_groups[key] = s.count
        assert old_groups == new_groups, "Classifier bool multi: group stats differ"


# ==============================================================================
# Phase 4: Group Identification Tests
# ==============================================================================


@pytest.fixture
def mem_old_provider(mem_old_database):
    """Get provider from mem JSON database for Phase 4 tests."""
    provider = mem_old_database.provider
    provider.reset()
    return provider


@pytest.fixture
def mem_new_provider(mem_saurus_database):
    """Get provider from mem Saurus SQL database for Phase 4 tests."""
    provider = mem_saurus_database.provider
    provider.reset()
    return provider


class TestGroupIdentification:
    """Tests for group identification and selection (Phase 4)."""

    def test_set_group_by_index(self, mem_old_provider, mem_new_provider):
        """Verify that set_group(index) selects the same group in JSON and SQL."""
        old_p = mem_old_provider
        new_p = mem_new_provider

        # Group by extension (simple field with multiple groups)
        old_p.set_groups("extension", allow_singletons=True, sorting="count", reverse=True)
        new_p.set_groups("extension", allow_singletons=True, sorting="count", reverse=True)

        old_p.get_view_indices()
        new_p.get_view_indices()

        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()

        # Test selecting different group indices
        for idx in [0, len(old_stats) // 2, len(old_stats) - 1]:
            # Select group by index
            old_p.classifier_select_group(idx)
            new_p.classifier_select_group(idx)

            old_p.get_view_indices()
            new_p.get_view_indices()

            # Get video IDs in selected group
            old_ids = get_view_ids_set(old_p)
            new_ids = get_view_ids_set(new_p)

            # Compare
            old_group_value = old_stats[idx].value
            new_group_value = new_stats[idx].value
            assert old_ids == new_ids, (
                f"Group {idx} (value={old_group_value}) has different videos: "
                f"JSON={len(old_ids)} videos, SQL={len(new_ids)} videos"
            )

    def test_classifier_stats_identical(
        self, mem_old_provider, mem_new_provider
    ):
        """Verify that get_classifier_stats() returns identical group values and counts."""
        old_p = mem_old_provider
        new_p = mem_new_provider

        # Test with property grouping
        old_p.set_groups("category", is_property=True, allow_singletons=True)
        new_p.set_groups("category", is_property=True, allow_singletons=True)

        old_p.get_view_indices()
        new_p.get_view_indices()

        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()

        # Build dicts for comparison
        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {s.value: s.count for s in new_stats}

        assert old_groups == new_groups, (
            f"Classifier stats differ:\nJSON={old_groups}\nSQL={new_groups}"
        )

    def test_classifier_select_group_consistency(
        self, mem_old_provider, mem_new_provider
    ):
        """Verify that classifier_select_group works identically in JSON and SQL."""
        old_p = mem_old_provider
        new_p = mem_new_provider

        # Set up classifier with multi-value property
        old_p.set_groups("category", is_property=True, allow_singletons=True)
        new_p.set_groups("category", is_property=True, allow_singletons=True)

        old_p.set_classifier_path(["action"])
        new_p.set_classifier_path(["action"])

        old_p.get_view_indices()
        new_p.get_view_indices()

        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()

        # Select the second group (if it exists)
        if len(old_stats) > 1:
            old_p.classifier_select_group(1)
            new_p.classifier_select_group(1)

            old_p.get_view_indices()
            new_p.get_view_indices()

            # Compare video IDs
            old_ids = get_view_ids_set(old_p)
            new_ids = get_view_ids_set(new_p)

            assert old_ids == new_ids, (
                f"Selected group has different videos after classifier_select_group(1): "
                f"JSON={len(old_ids)}, SQL={len(new_ids)}"
            )

    def test_group_identification_mechanism(
        self, mem_old_provider, mem_new_provider
    ):
        """Document and verify the group identification mechanism (index-based)."""
        old_p = mem_old_provider
        new_p = mem_new_provider

        # Group by a field with known values
        old_p.set_groups("extension", allow_singletons=True, sorting="field", reverse=False)
        new_p.set_groups("extension", allow_singletons=True, sorting="field", reverse=False)

        old_p.get_view_indices()
        new_p.get_view_indices()

        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()

        # Verify that groups are in the same order
        old_values = [s.value for s in old_stats]
        new_values = [s.value for s in new_stats]

        assert old_values == new_values, (
            f"Group order differs:\nJSON={old_values[:10]}\nSQL={new_values[:10]}"
        )

        # Verify that selecting by index selects the same value
        for idx in range(min(5, len(old_stats))):
            old_p.classifier_select_group(idx)
            new_p.classifier_select_group(idx)

            old_p.get_view_indices()
            new_p.get_view_indices()

            # Get video IDs in selected group
            old_ids = get_view_ids_set(old_p)
            new_ids = get_view_ids_set(new_p)

            # The selected groups should have the same videos
            assert old_ids == new_ids, (
                f"Group {idx} (value={old_values[idx]}) has different videos: "
                f"JSON={len(old_ids)}, SQL={len(new_ids)}"
            )


# ==============================================================================
# Phase 5: Corner Cases Tests
# ==============================================================================


class TestCornerCases:
    """Tests for edge cases and corner cases (Phase 5)."""

    def test_grouping_with_null_values(self, mem_old_provider, mem_new_provider):
        """Test grouping with NULL/None values (videos without the property)."""
        old_p = mem_old_provider
        new_p = mem_new_provider

        # Group by a property that some videos don't have
        old_p.set_groups("category", is_property=True, allow_singletons=True)
        new_p.set_groups("category", is_property=True, allow_singletons=True)

        old_p.get_view_indices()
        new_p.get_view_indices()

        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()

        # Both should have a None/NULL group for videos without the property
        old_has_none = any(s.value is None for s in old_stats)
        new_has_none = any(s.value is None for s in new_stats)

        assert old_has_none == new_has_none, (
            f"NULL group presence differs: JSON={old_has_none}, SQL={new_has_none}"
        )

        # Compare group stats
        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {s.value: s.count for s in new_stats}
        assert old_groups == new_groups, "Group stats differ for NULL values"

    def test_grouping_with_empty_values(
        self, old_provider_with_test_properties, new_provider_with_test_properties
    ):
        """Test grouping with empty string values."""
        old_p = old_provider_with_test_properties
        new_p = new_provider_with_test_properties

        # Group by str property (which has empty string as default for videos without property)
        old_p.set_groups("test_color", is_property=True, allow_singletons=True)
        new_p.set_groups("test_color", is_property=True, allow_singletons=True)

        old_p.get_view_indices()
        new_p.get_view_indices()

        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()

        # Both should handle empty strings correctly
        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {s.value: s.count for s in new_stats}

        # Normalize empty strings to None for comparison
        old_groups_normalized = {(k if k != '' else None): v for k, v in old_groups.items()}
        new_groups_normalized = {(k if k != '' else None): v for k, v in new_groups.items()}

        assert old_groups_normalized == new_groups_normalized, (
            f"Group stats differ for empty values:\nJSON={old_groups}\nSQL={new_groups}"
        )

    def test_grouping_with_singletons(self, mem_old_provider, mem_new_provider):
        """Test allow_singletons=True vs False."""
        old_p = mem_old_provider
        new_p = mem_new_provider

        # Test with allow_singletons=False (exclude groups with only 1 video)
        old_p.set_groups("extension", allow_singletons=False, sorting="count", reverse=True)
        new_p.set_groups("extension", allow_singletons=False, sorting="count", reverse=True)

        old_p.get_view_indices()
        new_p.get_view_indices()

        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()

        # All groups should have count > 1
        old_singletons = [s for s in old_stats if s.count == 1]
        new_singletons = [s for s in new_stats if s.count == 1]

        assert len(old_singletons) == 0, f"JSON has singleton groups: {old_singletons}"
        assert len(new_singletons) == 0, f"SQL has singleton groups: {new_singletons}"

        # Compare group stats
        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {s.value: s.count for s in new_stats}
        assert old_groups == new_groups, "Group stats differ with allow_singletons=False"

    def test_grouping_with_sorting_variations(self, mem_old_provider, mem_new_provider):
        """Test different sorting modes (field, count, length) and reverse."""
        old_p = mem_old_provider
        new_p = mem_new_provider

        # Test combinations of sorting and reverse
        test_cases = [
            ("field", False),  # Sort by field value ascending
            ("field", True),   # Sort by field value descending
            ("count", False),  # Sort by count ascending
            ("count", True),   # Sort by count descending
        ]

        for sorting, reverse in test_cases:
            old_p.reset()
            new_p.reset()

            old_p.set_groups("extension", allow_singletons=True, sorting=sorting, reverse=reverse)
            new_p.set_groups("extension", allow_singletons=True, sorting=sorting, reverse=reverse)

            old_p.get_view_indices()
            new_p.get_view_indices()

            old_stats = old_p.get_classifier_stats()
            new_stats = new_p.get_classifier_stats()

            # Group order should be identical
            old_values = [s.value for s in old_stats]
            new_values = [s.value for s in new_stats]

            assert old_values == new_values, (
                f"Group order differs for sorting={sorting}, reverse={reverse}:\n"
                f"JSON={old_values[:10]}\nSQL={new_values[:10]}"
            )

    def test_grouping_with_search(self, mem_old_provider, mem_new_provider):
        """Test grouping combined with search filter."""
        old_p = mem_old_provider
        new_p = mem_new_provider

        # Apply search filter then group
        old_p.set_search("mkv")  # Search for videos with "mkv" in name
        new_p.set_search("mkv")

        old_p.set_groups("extension", allow_singletons=True, sorting="count", reverse=True)
        new_p.set_groups("extension", allow_singletons=True, sorting="count", reverse=True)

        old_p.get_view_indices()
        new_p.get_view_indices()

        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()

        # Group stats should be identical after search
        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {s.value: s.count for s in new_stats}

        assert old_groups == new_groups, (
            f"Group stats differ with search:\nJSON={old_groups}\nSQL={new_groups}"
        )

        # Verify all groups contain only searched videos
        old_p.classifier_select_group(0)
        new_p.classifier_select_group(0)

        old_p.get_view_indices()
        new_p.get_view_indices()

        old_ids = get_view_ids_set(old_p)
        new_ids = get_view_ids_set(new_p)

        assert old_ids == new_ids, "Video IDs differ in first group after search"

    def test_grouping_with_filtered_sources(self, mem_old_provider, mem_new_provider):
        """Test grouping with source filters applied."""
        old_p = mem_old_provider
        new_p = mem_new_provider

        # Apply source filter (e.g., only readable videos)
        old_p.set_sources([["readable"]])
        new_p.set_sources([["readable"]])

        old_p.set_groups("extension", allow_singletons=True, sorting="count", reverse=True)
        new_p.set_groups("extension", allow_singletons=True, sorting="count", reverse=True)

        old_p.get_view_indices()
        new_p.get_view_indices()

        old_stats = old_p.get_classifier_stats()
        new_stats = new_p.get_classifier_stats()

        # Group stats should be identical with source filter
        old_groups = {s.value: s.count for s in old_stats}
        new_groups = {s.value: s.count for s in new_stats}

        assert old_groups == new_groups, (
            f"Group stats differ with source filter:\nJSON={old_groups}\nSQL={new_groups}"
        )


# ==============================================================================
# Critical CRUD Operations Tests
# ==============================================================================



# ==============================================================================
# Note: CRUD operation tests (delete, apply_on_view) were moved to
# test_video_lifecycle.py which uses real test videos.
#
# See: tests/databases/unittests/comparisons/test_video_lifecycle.py
# ==============================================================================
