"""
Unit tests for ViewContext state management.

These tests verify ViewContext behavior independently of any database.
"""

from pysaurus.dbview.view_context import ViewContext


class TestViewContextState:
    """Tests for ViewContext state management."""

    def test_default_state(self):
        view = ViewContext()
        assert view.sources
        assert view.grouping.field is None
        assert view.classifier == []
        assert view.group == 0

    def test_reset(self):
        view = ViewContext()
        view.set_search("test", "and")
        view.set_sort(["-file_size"])
        view.set_sources([["found"]])

        view.reset()

        fresh = ViewContext()
        assert view.sources == fresh.sources
        assert view.sorting == fresh.sorting
        assert view.search.text == fresh.search.text

    def test_set_sources(self):
        view = ViewContext()
        view.set_sources([["readable", "found"]])
        assert view.sources == [["readable", "found"]]

    def test_set_search(self):
        view = ViewContext()
        view.set_search("test query", "or")
        assert view.search.text == "test query"
        assert view.search.cond == "or"

    def test_set_sort(self):
        view = ViewContext()
        view.set_sort(["-width", "height"])
        assert view.sorting == ["-width", "height"]

    def test_set_grouping(self):
        view = ViewContext()
        view.set_grouping("extension", is_property=False, allow_singletons=True)
        assert view.grouping.field == "extension"
        assert view.grouping.is_property is False
        assert view.grouping.allow_singletons is True

    def test_set_grouping_resets_classifier_and_group(self):
        view = ViewContext()
        view.classifier = ["a", "b"]
        view.set_group(3)
        view.set_search("test", "and")

        view.set_grouping("width")

        assert view.classifier == []
        assert view.group == 0
        # Search is also reset by set_grouping cascade
        assert not view.search.text

    def test_classifier_select(self):
        view = ViewContext()
        view.set_grouping("category", is_property=True)
        view.classifier_select("thriller")
        assert view.classifier == ["thriller"]
        assert view.group == 0

    def test_classifier_select_multi(self):
        view = ViewContext()
        view.set_grouping("category", is_property=True)
        view.classifier_select("thriller")
        view.classifier_select("action")
        assert view.classifier == ["thriller", "action"]

    def test_classifier_back(self):
        view = ViewContext()
        view.classifier = ["thriller", "action"]
        view.classifier_back()
        assert view.classifier == ["thriller"]
        view.classifier_back()
        assert view.classifier == []

    def test_classifier_back_empty(self):
        view = ViewContext()
        view.classifier_back()
        assert view.classifier == []

    def test_classifier_reverse(self):
        view = ViewContext()
        view.classifier = ["a", "b", "c"]
        result = view.classifier_reverse()
        assert result == ["c", "b", "a"]
        assert view.classifier == ["c", "b", "a"]

    def test_set_group_negative(self):
        view = ViewContext()
        view.set_group(-1)
        assert view.group == 0

    def test_set_group_positive(self):
        view = ViewContext()
        view.set_group(5)
        assert view.group == 5
