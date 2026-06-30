"""Tests for videroid dialogs — focus on the result-building logic.

Each dialog is built with raw data (PropType / values / a real context) and its
state is driven by calling the same handlers its buttons call, then the getter
(`get_result` / `get_changes` / `get_folders` / `get_sources`) is checked.
"""

from pysaurus.interface.videroid.dialogs.batch_edit_property_dialog import (
    BatchEditPropertyDialog,
)
from pysaurus.interface.videroid.dialogs.edit_folders_dialog import EditFoldersDialog
from pysaurus.interface.videroid.dialogs.fill_property_dialog import FillPropertyDialog
from pysaurus.interface.videroid.dialogs.grouping_dialog import GroupingDialog
from pysaurus.interface.videroid.dialogs.move_values_dialog import MoveValuesDialog
from pysaurus.interface.videroid.dialogs.property_values_dialog import (
    PropertyValuesDialog,
)
from pysaurus.interface.videroid.dialogs.sorting_dialog import SortingDialog
from pysaurus.interface.videroid.dialogs.sources_dialog import SourcesDialog
from pysaurus.properties.properties import PropType


def _evt(**attrs):
    """A fake event/widget carrying `.data` (what on_click handlers read)."""
    return type("Evt", (), attrs)()


def _prop(name, type="str", multiple=False, enumeration=None):
    return PropType(
        name=name, type=type, multiple=multiple, default=[], enumeration=enumeration
    )


class TestBatchEditPropertyDialog:
    def test_initial_no_changes(self):
        d = BatchEditPropertyDialog(
            _prop("tags", multiple=True), 3, [["a", 2], ["b", 1]]
        )
        assert d.get_changes() == ([], [])

    def test_remove_existing_value(self):
        d = BatchEditPropertyDialog(
            _prop("tags", multiple=True), 3, [["a", 2], ["b", 1]]
        )
        d._remove(_evt(data="a"))
        to_add, to_remove = d.get_changes()
        assert to_add == [] and to_remove == ["a"]

    def test_add_existing_value_multiple(self):
        d = BatchEditPropertyDialog(
            _prop("tags", multiple=True), 3, [["a", 2], ["b", 1]]
        )
        d._add_existing(_evt(data="b"))
        to_add, to_remove = d.get_changes()
        assert to_add == ["b"] and to_remove == []

    def test_single_prop_promote_replaces_all(self):
        d = BatchEditPropertyDialog(
            _prop("cat", multiple=False), 3, [["a", 2], ["b", 1]]
        )
        d._editor.value = "c"
        d._on_add_new(None)
        to_add, to_remove = d.get_changes()
        assert to_add == ["c"]
        assert set(to_remove) == {"a", "b"}  # single value replaces everything

    def test_add_new_value_via_editor(self):
        d = BatchEditPropertyDialog(_prop("tags", multiple=True), 3, [["a", 2]])
        d._editor.value = "fresh"
        d._on_add_new(None)
        assert d.get_changes()[0] == ["fresh"]

    def test_remove_all(self):
        d = BatchEditPropertyDialog(
            _prop("tags", multiple=True), 3, [["a", 2], ["b", 1]]
        )
        d._remove_all(None)
        assert set(d.get_changes()[1]) == {"a", "b"}


class TestSortingDialog:
    def test_parse_roundtrip(self):
        assert SortingDialog(["-date"]).get_result() == ["-date"]

    def test_toggle_flips_direction(self):
        d = SortingDialog(["-date"])
        d._toggle(_evt(data=0))
        assert d.get_result() == ["+date"]

    def test_remove_criterion(self):
        d = SortingDialog(["-date"])
        d._remove(_evt(data=0))
        assert d.get_result() == []

    def test_add_criterion(self):
        d = SortingDialog([])
        d._dropdown.index = 0
        d._add_asc(None)
        result = d.get_result()
        assert len(result) == 1 and result[0].startswith("+")

    def test_reorder_up(self):
        d = SortingDialog(["+a_field", "+b_field"])
        criteria_before = [c[0] for c in d._criteria]
        d._up(_evt(data=1))
        criteria_after = [c[0] for c in d._criteria]
        assert criteria_after == list(reversed(criteria_before))


class TestGroupingDialog:
    def test_default_result(self):
        result = GroupingDialog(["category"]).get_result()
        assert result["is_property"] is False
        assert result["sorting"] == "field"
        assert result["reverse"] is False
        assert result["allow_singletons"] is False  # default unchecked (== pyside6)

    def test_select_property_option(self):
        d = GroupingDialog(["category"])
        prop_index = next(
            i
            for i, (_, name, is_p) in enumerate(d._options)
            if is_p and name == "category"
        )
        d._field.index = prop_index
        result = d.get_result()
        assert result["field"] == "category" and result["is_property"] is True

    def test_reverse_checkbox(self):
        d = GroupingDialog([])
        d._reverse.checked = True
        assert d.get_result()["reverse"] is True

    def test_prefill_from_current(self):
        from pysaurus.dbview.view_tools import GroupDef

        d = GroupingDialog(["category"], current=GroupDef("category", is_property=True))
        _, name, is_p = d._options[d._field.index]
        assert name == "category" and is_p is True


class TestFillPropertyDialog:
    def test_no_eligible_property(self):
        # Only str+multiple props are eligible.
        d = FillPropertyDialog([_prop("n", type="int"), _prop("s", multiple=False)])
        assert d.get_result() is None

    def test_eligible_property_and_only_empty_flag(self):
        eligible = _prop("keywords", type="str", multiple=True)
        d = FillPropertyDialog([_prop("n", type="int"), eligible])
        prop, only_empty = d.get_result()
        assert prop.name == "keywords"
        assert only_empty is False  # default unchecked (== pyside6)
        d._only_empty.checked = True
        assert d.get_result()[1] is True  # the checkbox value is actually read


class TestEditFoldersDialog:
    def test_get_folders_roundtrip(self):
        d = EditFoldersDialog(["/a", "/b"])
        assert d.get_folders() == ["/a", "/b"]

    def test_remove_folder(self):
        d = EditFoldersDialog(["/a", "/b"])
        d._remove(_evt(data="/a"))
        assert d.get_folders() == ["/b"]

    def test_add_dedups(self):
        d = EditFoldersDialog([])
        d._add("/some/path")
        d._add("/some/path")  # same normalized path: ignored
        assert len(d.get_folders()) == 1


class TestSourcesDialog:
    def test_default_selects_valid(self):
        assert SourcesDialog().get_sources() == [
            ["readable", "found", "with_thumbnails"]
        ]

    def test_checking_a_source(self):
        d = SourcesDialog()
        d._checkboxes["unreadable.found"].checked = True
        assert ["unreadable", "found"] in d.get_sources()

    def test_expression_passthrough(self):
        assert SourcesDialog(current_expression="width > 1").get_expression() == (
            "width > 1"
        )
        assert SourcesDialog().get_expression() is None

    def test_is_advanced_after_tab_switch(self):
        d = SourcesDialog()
        assert d.is_advanced() is False
        d._tabs._on_click(_evt(data=1))
        assert d.is_advanced() is True


class TestMoveValuesDialog:
    def test_no_target_or_selection_returns_none(self, videroid_context):
        source = next(p for p in videroid_context.get_prop_types())
        dialog = MoveValuesDialog(videroid_context, source)
        assert dialog.get_result() is None  # nothing selected

    def test_result_with_selection(self, videroid_context):
        videroid_context.create_prop_type("msrc", "str", "", True)
        videroid_context.create_prop_type("mdst", "str", "", False)
        source = next(p for p in videroid_context.get_prop_types() if p.name == "msrc")
        dialog = MoveValuesDialog(videroid_context, source)
        target_names = {p.name for p in dialog._targets}
        assert "mdst" in target_names and "msrc" not in target_names
        dialog._selected.add("x")
        values, target, concat = dialog.get_result()
        assert values == ["x"] and concat is False


class TestPropertyValuesDialog:
    def test_stats_and_delete(self, videroid_context):
        data = videroid_context.get_property_values("category")
        all_values = [v for values in data.values() for v in values]
        if not all_values:
            return  # nothing to delete in this database
        value = all_values[0]
        dialog = PropertyValuesDialog(videroid_context, "category")
        assert "unique values" in dialog._stats.text
        dialog._selected.add(value)
        dialog._do_delete([value])
        after = videroid_context.get_property_values("category")
        assert value not in {v for vals in after.values() for v in vals}
