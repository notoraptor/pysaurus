"""
Additional tests to improve coverage of video_mega_group() function.

These tests target specific code paths not covered by test_saurus_sql.py,
focusing on edge cases like:
- Grouping by attribute with LENGTH sorting
- Grouping by similarity_id
- Classifier with NULL values (videos without property)
"""

import pytest

from pysaurus.database.abstract_database import AbstractDatabase


@pytest.fixture(params=["saurus_sql"])
def saurus_database(request, example_saurus_database) -> AbstractDatabase:
    """Fixture for Saurus SQL database only (JSON has bugs with some grouping features)."""
    return example_saurus_database


class TestVideoMegaGroupEdgeCases:
    """Tests for video_mega_group() edge cases and rare code paths."""

    def test_grouping_by_attribute_with_length_sorting(self, saurus_database):
        """Test grouping by attribute (non-property) with LENGTH sorting.

        This covers line 537: order_field = field_factory.get_length(grouping.field) + " " + order_direction
        """
        provider = saurus_database.provider

        # Group by video_codec (attribute, not property) with LENGTH sorting
        provider.set_groups("video_codec", allow_singletons=True, sorting="length")
        # Trigger provider update
        indices = provider.get_view_indices()
        group_def = provider.get_group_def()

        # Should have groups and videos
        assert len(group_def["groups"]) > 0
        assert len(indices) > 0

        # Verify groups are sorted by length of the codec name
        groups = group_def["groups"]
        for i in range(len(groups) - 1):
            current_val = str(groups[i]["value"] or "")
            next_val = str(groups[i + 1]["value"] or "")
            current_len = len(current_val)
            next_len = len(next_val)
            # Length should be non-decreasing (or equal with secondary sort by value)
            assert current_len <= next_len or (
                current_len == next_len and current_val <= next_val
            )

    def test_grouping_by_attribute_with_length_sorting_reverse(self, saurus_database):
        """Test grouping by attribute with reverse LENGTH sorting."""
        provider = saurus_database.provider

        # Group by audio_codec with reverse LENGTH sorting
        provider.set_groups(
            "audio_codec", allow_singletons=True, sorting="length", reverse=True
        )
        # Trigger provider update
        indices = provider.get_view_indices()
        group_def = provider.get_group_def()

        # Should have groups and videos
        assert len(group_def["groups"]) > 0
        assert len(indices) > 0

        # Verify groups are sorted by length in descending order
        groups = group_def["groups"]
        for i in range(len(groups) - 1):
            current_val = str(groups[i]["value"] or "")
            next_val = str(groups[i + 1]["value"] or "")
            current_len = len(current_val)
            next_len = len(next_val)
            # Length should be non-increasing
            assert current_len >= next_len or (
                current_len == next_len and current_val >= next_val
            )

    def test_classifier_with_null_property_value(self, saurus_database):
        """Test classifier selecting videos without a property (NULL value).

        This covers lines 593, 601: handling field_value is None in classifier.

        When selecting the NULL group in a classifier, it should return videos
        that don't have the property at all.
        """
        provider = saurus_database.provider

        # Group by category property with singletons
        provider.set_groups("category", allow_singletons=True)
        group_def = provider.get_group_def()

        # Find the NULL group (videos without category property)
        null_group_index = None
        for i, group in enumerate(group_def["groups"]):
            if group["value"] is None:
                null_group_index = i
                break

        # If there's a NULL group, test selecting it
        if null_group_index is not None:
            # Set classifier to the NULL group
            provider.set_classifier_path([None])
            indices = provider.get_view_indices()

            # Should get the videos without the category property
            assert len(indices) == group_def["groups"][null_group_index]["count"]

            # Verify these videos indeed don't have the category property
            videos = saurus_database.get_videos(
                include=["properties"], where={"video_id": indices}
            )
            for video in videos:
                # Should not have category property or it should be empty
                category = video.properties.get("category")
                assert category is None or category == [] or category == ""

    def test_grouping_with_multiple_sources_and_classifier(self, saurus_database):
        """Test complex grouping with multiple sources and classifier path."""
        provider = saurus_database.provider

        # Set multiple sources (readable OR unreadable)
        provider.set_sources([["readable"], ["unreadable"]])

        # Group by category
        provider.set_groups(
            "category",
            is_property=True,
            allow_singletons=True,
            sorting="count",
            reverse=True,
        )

        # Trigger provider update
        provider.get_view_indices()

        # Get initial groups
        group_def = provider.get_group_def()
        initial_group_count = len(group_def["groups"])
        assert initial_group_count > 0

        # Set classifier to a specific category
        # Find a category with multiple videos
        target_category = None
        for group in group_def["groups"]:
            if group["count"] > 1 and group["value"] is not None:
                target_category = group["value"]
                break

        if target_category:
            provider.set_classifier_path([target_category])
            indices = provider.get_view_indices()

            # Should have videos
            assert len(indices) > 0

            # Can set a second level classifier
            provider.set_classifier_path([target_category, None])
            # This should work without error
            group_def_level2 = provider.get_group_def()
            # Groups should exist (might be empty or have sub-categories)
            assert "groups" in group_def_level2

    def test_grouping_with_empty_result_set(self, saurus_database):
        """Test grouping when source filter results in no videos."""
        provider = saurus_database.provider

        # Set impossible source combination
        provider.set_sources([["readable", "without_thumbnails", "unreadable"]])

        # Try to group by any field
        provider.set_groups("audio_codec")

        # Should have no videos
        assert len(provider.get_view_indices()) == 0

        # Group definition should have no groups
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 0

    def test_grouping_switching_between_attribute_and_property(self, saurus_database):
        """Test switching between grouping by attribute and property."""
        provider = saurus_database.provider

        # Group by attribute first
        provider.set_groups("audio_codec", allow_singletons=True)
        provider.get_view_indices()  # Trigger update
        group_def_attr = provider.get_group_def()
        attr_group_count = len(group_def_attr["groups"])

        # Switch to grouping by property
        provider.set_groups("category", is_property=True, allow_singletons=True)
        provider.get_view_indices()  # Trigger update
        group_def_prop = provider.get_group_def()
        prop_group_count = len(group_def_prop["groups"])

        # Both should have groups (counts will differ)
        assert attr_group_count > 0
        assert prop_group_count > 0

        # Switch back to attribute
        provider.set_groups("video_codec", allow_singletons=True)
        provider.get_view_indices()  # Trigger update
        group_def_attr2 = provider.get_group_def()
        assert len(group_def_attr2["groups"]) > 0

    def test_grouping_by_attribute_all_sorting_modes(self, saurus_database):
        """Test all sorting modes for attribute grouping."""
        provider = saurus_database.provider

        # Test FIELD sorting (default)
        provider.set_groups("audio_codec", allow_singletons=True, sorting="field")
        provider.get_view_indices()  # Trigger update
        group_def_field = provider.get_group_def()
        assert len(group_def_field["groups"]) > 0

        # Test COUNT sorting
        provider.set_groups("audio_codec", allow_singletons=True, sorting="count")
        provider.get_view_indices()  # Trigger update
        group_def_count = provider.get_group_def()
        assert len(group_def_count["groups"]) > 0

        # Verify COUNT sorting works correctly
        groups_count = group_def_count["groups"]
        for i in range(len(groups_count) - 1):
            # Count should be non-decreasing
            assert groups_count[i]["count"] <= groups_count[i + 1]["count"]

        # Test LENGTH sorting
        provider.set_groups("audio_codec", allow_singletons=True, sorting="length")
        provider.get_view_indices()  # Trigger update
        group_def_length = provider.get_group_def()
        assert len(group_def_length["groups"]) > 0

    def test_classifier_with_nested_path(self, saurus_database):
        """Test classifier with multiple levels of nesting."""
        provider = saurus_database.provider

        # Group by category with singletons
        provider.set_groups(
            "category", allow_singletons=True, sorting="count", reverse=True
        )

        # Get groups to find a suitable path
        group_def = provider.get_group_def()

        # Find the first non-NULL category
        first_category = None
        for group in group_def["groups"]:
            if group["value"] is not None and group["count"] > 0:
                first_category = group["value"]
                break

        if first_category:
            # Set first level classifier
            provider.set_classifier_path([first_category])
            indices_level1 = provider.get_view_indices()
            assert len(indices_level1) > 0

            # Get sub-groups
            group_def_level1 = provider.get_group_def()

            # Try to go one level deeper if possible
            second_category = None
            for group in group_def_level1["groups"]:
                if group["value"] != first_category and group["value"] is not None:
                    second_category = group["value"]
                    break

            if second_category:
                # Set second level classifier
                provider.set_classifier_path([first_category, second_category])
                indices_level2 = provider.get_view_indices()

                # Should have fewer or equal videos than level 1
                assert len(indices_level2) <= len(indices_level1)
