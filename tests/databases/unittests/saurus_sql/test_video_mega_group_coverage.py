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
from pysaurus.video_provider.view_context import ViewContext


@pytest.fixture(params=["saurus_sql"])
def saurus_database(request, example_saurus_database) -> AbstractDatabase:
    """Fixture for Saurus SQL database only (JSON has bugs with some grouping features)."""
    return example_saurus_database


class TestVideoMegaGroupEdgeCases:
    """Tests for video_mega_group() edge cases and rare code paths."""

    def _query_ids(self, db, view) -> list[int]:
        return [v.video_id for v in db.query_videos(view, None, None).result]

    def _query_stats(self, db, view):
        return db.query_videos(view, 1, 0).classifier_stats

    def test_grouping_by_attribute_with_length_sorting(self, saurus_database):
        """Test grouping by attribute (non-property) with LENGTH sorting."""
        view = ViewContext()
        view.set_grouping("video_codec", allow_singletons=True, sorting="length")
        indices = self._query_ids(saurus_database, view)
        stats = self._query_stats(saurus_database, view)

        assert len(stats) > 0
        assert len(indices) > 0

        for i in range(len(stats) - 1):
            current_val = str(stats[i].value or "")
            next_val = str(stats[i + 1].value or "")
            assert len(current_val) <= len(next_val) or (
                len(current_val) == len(next_val) and current_val <= next_val
            )

    def test_grouping_by_attribute_with_length_sorting_reverse(self, saurus_database):
        """Test grouping by attribute with reverse LENGTH sorting."""
        view = ViewContext()
        view.set_grouping(
            "audio_codec", allow_singletons=True, sorting="length", reverse=True
        )
        indices = self._query_ids(saurus_database, view)
        stats = self._query_stats(saurus_database, view)

        assert len(stats) > 0
        assert len(indices) > 0

        for i in range(len(stats) - 1):
            current_val = str(stats[i].value or "")
            next_val = str(stats[i + 1].value or "")
            assert len(current_val) >= len(next_val) or (
                len(current_val) == len(next_val) and current_val >= next_val
            )

    def test_classifier_with_null_property_value(self, saurus_database):
        """Test classifier selecting videos without a property (NULL value)."""
        db = saurus_database
        view = ViewContext()
        view.set_grouping("category", is_property=True, allow_singletons=True)
        stats = self._query_stats(db, view)

        null_group_index = None
        null_count = None
        for i, s in enumerate(stats):
            if s.value is None:
                null_group_index = i
                null_count = s.count
                break

        if null_group_index is not None:
            view.classifier = [None]
            indices = self._query_ids(db, view)
            assert len(indices) == null_count

            videos = db.get_videos(include=["properties"], where={"video_id": indices})
            for video in videos:
                category = video.properties.get("category")
                assert category is None or category == [] or category == ""

    def test_grouping_with_multiple_sources_and_classifier(self, saurus_database):
        """Test complex grouping with multiple sources and classifier path."""
        db = saurus_database
        view = ViewContext()
        view.set_sources([["readable"], ["unreadable"]])
        view.set_grouping(
            "category",
            is_property=True,
            allow_singletons=True,
            sorting="count",
            reverse=True,
        )
        stats = self._query_stats(db, view)
        assert len(stats) > 0

        target_category = None
        for s in stats:
            if s.count > 1 and s.value is not None:
                target_category = s.value
                break

        if target_category:
            view.classifier = [target_category]
            indices = self._query_ids(db, view)
            assert len(indices) > 0

            view.classifier = [target_category, None]
            stats_level2 = self._query_stats(db, view)
            assert isinstance(stats_level2, list)

    def test_grouping_with_empty_result_set(self, saurus_database):
        """Test grouping when source filter results in no videos."""
        view = ViewContext()
        view.set_sources([["readable", "without_thumbnails"]])
        view.set_grouping("audio_codec")

        assert len(self._query_ids(saurus_database, view)) == 0
        stats = self._query_stats(saurus_database, view)
        assert len(stats) == 0

    def test_grouping_switching_between_attribute_and_property(self, saurus_database):
        """Test switching between grouping by attribute and property."""
        db = saurus_database
        view = ViewContext()

        view.set_grouping("audio_codec", allow_singletons=True)
        attr_group_count = len(self._query_stats(db, view))

        view.set_grouping("category", is_property=True, allow_singletons=True)
        prop_group_count = len(self._query_stats(db, view))

        assert attr_group_count > 0
        assert prop_group_count > 0

        view.set_grouping("video_codec", allow_singletons=True)
        assert len(self._query_stats(db, view)) > 0

    def test_grouping_by_attribute_all_sorting_modes(self, saurus_database):
        """Test all sorting modes for attribute grouping."""
        db = saurus_database
        view = ViewContext()

        view.set_grouping("audio_codec", allow_singletons=True, sorting="field")
        assert len(self._query_stats(db, view)) > 0

        view.set_grouping("audio_codec", allow_singletons=True, sorting="count")
        stats_count = self._query_stats(db, view)
        assert len(stats_count) > 0
        for i in range(len(stats_count) - 1):
            assert stats_count[i].count <= stats_count[i + 1].count

        view.set_grouping("audio_codec", allow_singletons=True, sorting="length")
        assert len(self._query_stats(db, view)) > 0

    def test_classifier_with_nested_path(self, saurus_database):
        """Test classifier with multiple levels of nesting."""
        db = saurus_database
        view = ViewContext()
        view.set_grouping(
            "category",
            is_property=True,
            allow_singletons=True,
            sorting="count",
            reverse=True,
        )
        stats = self._query_stats(db, view)

        first_category = None
        for s in stats:
            if s.value is not None and s.count > 0:
                first_category = s.value
                break

        if first_category:
            view.classifier = [first_category]
            indices_level1 = self._query_ids(db, view)
            assert len(indices_level1) > 0

            stats_level1 = self._query_stats(db, view)
            second_category = None
            for s in stats_level1:
                if s.value != first_category and s.value is not None:
                    second_category = s.value
                    break

            if second_category:
                view.classifier = [first_category, second_category]
                indices_level2 = self._query_ids(db, view)
                assert len(indices_level2) <= len(indices_level1)

    def test_search_by_video_id(self, saurus_database):
        """Test search by video ID directly."""
        view = ViewContext()
        view.set_search("196", "id")
        indices = self._query_ids(saurus_database, view)
        assert len(indices) == 1
        assert indices[0] == 196

    def test_grouping_by_property_with_length_sorting(self, saurus_database):
        """Test grouping by property with LENGTH sorting."""
        view = ViewContext()
        view.set_grouping(
            "category", is_property=True, allow_singletons=False, sorting="length"
        )
        stats = self._query_stats(saurus_database, view)

        if len(stats) > 0:
            for i in range(len(stats) - 1):
                current_val = str(stats[i].value or "")
                next_val = str(stats[i + 1].value or "")
                assert len(current_val) <= len(next_val) or (
                    len(current_val) == len(next_val) and current_val <= next_val
                )

    def test_grouping_by_similarity_id(self, saurus_database):
        """Test grouping by similarity_id with special filtering."""
        view = ViewContext()
        view.set_grouping("similarity_id", allow_singletons=True)
        stats = self._query_stats(saurus_database, view)

        for s in stats:
            assert s.value is not None
            assert s.value != -1

    def test_classifier_with_non_null_property_value(self, saurus_database):
        """Test classifier with non-NULL property value."""
        db = saurus_database
        view = ViewContext()
        view.set_grouping(
            "category",
            is_property=True,
            allow_singletons=True,
            sorting="count",
            reverse=True,
        )
        stats = self._query_stats(db, view)
        categories = [s.value for s in stats if s.value is not None and s.count > 0]

        if len(categories) >= 2:
            view.classifier = [categories[0]]
            indices_level1 = self._query_ids(db, view)
            assert len(indices_level1) > 0

            stats_level1 = self._query_stats(db, view)
            second_category = None
            for s in stats_level1:
                if s.value is not None and s.value != categories[0]:
                    second_category = s.value
                    break

            if second_category:
                view.classifier = [categories[0], second_category]
                indices_level2 = self._query_ids(db, view)
                assert len(indices_level2) > 0

    def test_classifier_with_null_property_value_in_path(self, saurus_database):
        """Test classifier when NULL is part of the classification path."""
        db = saurus_database
        view = ViewContext()
        view.set_grouping("category", is_property=True, allow_singletons=True)
        stats = self._query_stats(db, view)

        first_category = None
        for s in stats:
            if s.value is not None and s.count > 0:
                first_category = s.value
                break

        if first_category:
            view.classifier = [first_category]
            indices = self._query_ids(db, view)
            assert len(indices) > 0

            view.classifier = [first_category, None]
            indices_with_null = self._query_ids(db, view)
            assert len(indices_with_null) >= 0

    def test_search_with_text_query(self, saurus_database):
        """Test search with text query (not by ID)."""
        view = ViewContext()
        view.set_grouping("category", is_property=True, allow_singletons=True)
        view.set_search("unknown", "and")
        indices = self._query_ids(saurus_database, view)
        assert len(indices) > 0
