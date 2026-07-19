"""Unit tests for Selector (core/classes.py): cross-page selection state."""

from pysaurus.core.classes import Selector


class TestSelectorHasMarks:
    def test_empty_include_has_no_marks(self):
        assert not Selector(False, set()).has_marks()

    def test_select_all_has_no_marks(self):
        selector = Selector(False, {1, 2})
        selector.select_all()
        assert not selector.has_marks()

    def test_included_and_excluded_ids_are_marks(self):
        assert Selector(False, {1}).has_marks()
        assert Selector(True, {1}).has_marks()


class TestSelectorRestrictTo:
    def test_include_mode_drops_ids_absent_from_values(self):
        selector = Selector(False, {1, 2, 99})
        selector.restrict_to({1, 2, 3, 4})
        assert selector.contains(1)
        assert selector.contains(2)
        assert not selector.contains(99)
        assert selector.size_from(4) == 2

    def test_exclude_mode_drops_ids_absent_from_values(self):
        # An excluded id that left the view must stop counting against the
        # total: 4 in view, only 1 still-present exclusion -> 3 selected.
        selector = Selector(True, {1, 99})
        selector.restrict_to({1, 2, 3, 4})
        assert not selector.contains(1)
        assert selector.contains(2)
        assert selector.size_from(4) == 3

    def test_restrict_to_empty_view_drops_all_marks(self):
        selector = Selector(False, {1, 2})
        selector.restrict_to(set())
        assert not selector.has_marks()
        assert selector.size_from(0) == 0
