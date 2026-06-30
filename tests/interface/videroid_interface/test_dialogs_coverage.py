"""Extra dialog tests filling the remaining branches (state transitions, inline
actions, per-type editors, native pickers) toward full coverage.

Note: videre's `Container.control = None` resolves to an EmptyWidget, not None,
so inline-prompt assertions check the prompt's actual type (Row / Text).
"""

import videre

from pysaurus.interface.videroid.dialogs.batch_edit_property_dialog import (
    BatchEditPropertyDialog,
)
from pysaurus.interface.videroid.dialogs.edit_folders_dialog import EditFoldersDialog
from pysaurus.interface.videroid.dialogs.move_values_dialog import MoveValuesDialog
from pysaurus.interface.videroid.dialogs.property_values_dialog import (
    PropertyValuesDialog,
)
from pysaurus.interface.videroid.dialogs.sorting_dialog import SortingDialog
from pysaurus.interface.videroid.dialogs.sources_dialog import SourcesDialog
from pysaurus.properties.properties import PropType
from pysaurus.properties.property_value_modifier import PropertyValueModifier
from tests.interface.videroid_interface._widget_tree import find as _find


def _evt(**attrs):
    return type("Evt", (), attrs)()


def _prop(name, type="str", multiple=False, enumeration=None):
    return PropType(
        name=name, type=type, multiple=multiple, default=[], enumeration=enumeration
    )


def _batch(prop_kwargs, values=None):
    return BatchEditPropertyDialog(_prop("p", **prop_kwargs), 1, values or [])


class TestBatchEditEditors:
    def test_enum_editor_selection_promotes(self):
        d = _batch(dict(enumeration=["x", "y"]))
        assert isinstance(d._editor, videre.Dropdown)
        d._editor.index = 1  # pick "y" from the enum dropdown
        d._on_add_new(None)
        assert d.get_changes()[0] == ["y"]  # the chosen enum value is staged

    def test_bool_editor_reads_true(self):
        d = _batch(dict(type="bool"))
        assert isinstance(d._editor, videre.Dropdown)
        d._on_add_new(None)  # default selection "true" -> True
        assert d.get_changes()[0] == [True]

    def test_int_valid_value(self):
        d = _batch(dict(type="int", multiple=True))
        d._editor.value = "42"
        d._on_add_new(None)
        assert d.get_changes()[0] == [42]

    def test_float_valid_value(self):
        d = _batch(dict(type="float", multiple=True))
        d._editor.value = "1.5"
        d._on_add_new(None)
        assert d.get_changes()[0] == [1.5]

    def test_int_invalid_value_sets_error(self):
        d = _batch(dict(type="int"))
        d._editor.value = "abc"
        d._on_add_new(None)
        assert d.get_changes() == ([], [])
        assert d._error.text

    def test_empty_value_ignored(self):
        d = _batch(dict(multiple=True))
        d._editor.value = "   "
        d._on_add_new(None)
        assert d.get_changes()[0] == []


class TestBatchEditTransitions:
    def test_restore_after_remove(self):
        d = _batch(dict(multiple=True), [["a", 1]])
        d._remove(_evt(data="a"))
        d._restore(_evt(data="a"))
        assert d.get_changes() == ([], [])

    def test_cancel_add(self):
        d = _batch(dict(multiple=True), [["a", 1]])
        d._add_existing(_evt(data="a"))
        d._cancel_add(_evt(data="a"))
        assert d.get_changes()[0] == []

    def test_promote_removed_value_restores_it(self):
        d = _batch(dict(multiple=True), [["a", 1]])
        d._remove(_evt(data="a"))  # "a" moved to 'To remove'
        d._editor.value = "a"
        d._on_add_new(None)  # re-typing restores it to current (== kyuti)...
        assert d.get_changes() == ([], [])  # ...not a force-add to every video
        assert "a" in d._current

    def test_restore_all(self):
        d = _batch(dict(multiple=True), [["a", 1], ["b", 1]])
        d._remove_all(None)
        d._restore_all(None)
        assert d.get_changes()[1] == []

    def test_add_all(self):
        d = _batch(dict(multiple=True), [["a", 1], ["b", 1]])
        d._add_all(None)
        assert set(d.get_changes()[0]) == {"a", "b"}

    def test_cancel_all(self):
        d = _batch(dict(multiple=True), [["a", 1]])
        d._add_existing(_evt(data="a"))
        d._cancel_all(None)
        assert d.get_changes()[0] == []


class TestSortingExtra:
    def test_down(self):
        d = SortingDialog(["+a", "+b"])
        d._down(_evt(data=0))
        assert [c[0] for c in d._criteria] == ["b", "a"]

    def test_add_desc(self):
        d = SortingDialog([])
        d._dropdown.index = 0
        d._add_desc(None)
        assert d.get_result()[0].startswith("-")


class TestSourcesExtra:
    def test_load_current_checks_matching_source(self):
        d = SourcesDialog(current_sources=[["unreadable", "found"]])
        assert d._checkboxes["unreadable.found"].checked

    def test_select_all(self):
        d = SourcesDialog()
        d._select_all(None)
        assert all(cb.checked for cb in d._checkboxes.values())

    def test_select_none(self):
        d = SourcesDialog()
        d._select_none(None)
        assert not any(cb.checked for cb in d._checkboxes.values())

    def test_select_valid_keeps_one(self):
        d = SourcesDialog()
        d._select_all(None)
        d._select_valid(None)
        assert sum(cb.checked for cb in d._checkboxes.values()) == 1

    def test_advanced_tab_shows_expression_input(self):
        d = SourcesDialog(current_expression="w>1")
        d._tabs._on_click(_evt(data=1))
        assert d.is_advanced()
        # The advanced tab really built its content: the expression input is in it.
        assert d._expression in _find(d._tabs._holder.control, videre.TextInput)


class TestEditFoldersExtra:
    def test_add_empty_ignored(self):
        d = EditFoldersDialog([])
        d._add("")
        assert d.get_folders() == []

    def test_add_folder_via_picker(self, monkeypatch):
        monkeypatch.setattr("videre.Dialog.select_directory", staticmethod(lambda: "x"))
        d = EditFoldersDialog([])
        d._add_folder(None)
        assert len(d.get_folders()) == 1

    def test_add_file_via_picker(self, monkeypatch):
        monkeypatch.setattr(
            "videre.Dialog.select_many_files", staticmethod(lambda: ["a", "b"])
        )
        d = EditFoldersDialog([])
        d._add_file(None)
        assert len(d.get_folders()) == 2


class TestMoveValuesExtra:
    def test_on_check_toggles_selection(self, videroid_context):
        videroid_context.create_prop_type("ms", "str", "", True)
        source = next(p for p in videroid_context.get_prop_types() if p.name == "ms")
        d = MoveValuesDialog(videroid_context, source)
        d._on_check(_evt(checked=True, data="v"))
        assert "v" in d._selected
        d._on_check(_evt(checked=False, data="v"))
        assert "v" not in d._selected


class TestPropertyValuesExtra:
    def _value(self, ctx):
        data = ctx.get_property_values("category")
        values = [v for vals in data.values() for v in vals]
        return values[0] if values else None

    def test_check_then_uncheck(self, videroid_context):
        d = PropertyValuesDialog(videroid_context, "category")
        d._on_check(_evt(checked=True, data="x"))
        assert "x" in d._selected
        d._on_check(_evt(checked=False, data="x"))
        assert "x" not in d._selected

    def test_ask_delete_empty_is_noop(self, videroid_context):
        d = PropertyValuesDialog(videroid_context, "category")
        d._ask_delete(None)  # nothing selected -> early return, no prompt row
        assert not isinstance(d._prompt.control, videre.Row)

    def test_delete_prompt_then_clear(self, videroid_context):
        value = self._value(videroid_context)
        if value is None:
            return
        d = PropertyValuesDialog(videroid_context, "category")
        d._on_check(_evt(checked=True, data=value))
        d._ask_delete(None)
        assert isinstance(d._prompt.control, videre.Row)  # inline Yes/No prompt
        d._clear_prompt()
        assert not isinstance(d._prompt.control, videre.Row)  # cleared

    def test_delete_via_yes_button(self, videroid_context):
        value = self._value(videroid_context)
        if value is None:
            return
        d = PropertyValuesDialog(videroid_context, "category")
        d._selected.add(value)
        d._ask_delete(None)
        # prompt Row is [message, "Yes", "No"]; fire the Yes callback directly.
        yes_button = d._prompt.control.controls[1]
        yes_button.on_click(yes_button)  # yes -> on_yes -> _do_delete
        flat = {
            v
            for vals in videroid_context.get_property_values("category").values()
            for v in vals
        }
        assert value not in flat

    def test_rename_prompt_and_apply(self, videroid_context):
        value = self._value(videroid_context)
        if value is None:
            return
        d = PropertyValuesDialog(videroid_context, "category")
        d._on_check(_evt(checked=True, data=value))
        d._ask_rename(None)
        assert isinstance(d._prompt.control, videre.Row)  # rename input row
        d._do_rename(value, videre.TextInput(f"{value}_renamed"))
        flat = {
            v
            for vals in videroid_context.get_property_values("category").values()
            for v in vals
        }
        assert f"{value}_renamed" in flat and value not in flat

    def test_rename_requires_single_selection(self, videroid_context):
        d = PropertyValuesDialog(videroid_context, "category")
        d._ask_rename(None)  # nothing selected -> error Text, not a rename Row
        assert isinstance(d._prompt.control, videre.Text)

    def test_modifier_lowercases_all_values(self, videroid_context):
        ctx = videroid_context
        db = ctx._api.database
        vid = ctx.get_videos(1, 0).result[0].video_id
        with db.to_save():
            db.videos_tag_set("category", {vid: ["HELLO"]})  # seed an uppercase value
        assert "lowercase" in PropertyValueModifier.get_modifiers()
        d = PropertyValuesDialog(ctx, "category")
        d._ask_modifier(_evt(data="lowercase"))
        assert isinstance(d._prompt.control, videre.Row)  # inline confirm prompt
        d._do_modifier("lowercase")  # apply + reload
        flat = {
            v for vals in ctx.get_property_values("category").values() for v in vals
        }
        assert "hello" in flat and "HELLO" not in flat  # really lowercased
