"""
Tests for BatchEditDialog and its helper widgets.

Tests the dialog for batch editing properties of multiple videos,
including MultipleValuesWidget (free-form and enum modes) and
NonSubmittingLineEdit.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent

from pysaurus.properties.properties import PropType


# -- Fixtures --


@pytest.fixture
def str_prop():
    return PropType(
        name="title", type="str", multiple=False, default=[""], enumeration=None
    )


@pytest.fixture
def bool_prop():
    return PropType(
        name="watched", type="bool", multiple=False, default=[False], enumeration=None
    )


@pytest.fixture
def int_prop():
    return PropType(
        name="rating", type="int", multiple=False, default=[0], enumeration=None
    )


@pytest.fixture
def float_prop():
    return PropType(
        name="score", type="float", multiple=False, default=[0.0], enumeration=None
    )


@pytest.fixture
def str_multiple_prop():
    return PropType(
        name="tags", type="str", multiple=True, default=[], enumeration=None
    )


@pytest.fixture
def enum_prop():
    return PropType(
        name="status",
        type="str",
        multiple=False,
        default=["new"],
        enumeration=["new", "watched", "archived"],
    )


@pytest.fixture
def enum_multiple_prop():
    return PropType(
        name="categories",
        type="str",
        multiple=True,
        default=[],
        enumeration=["action", "comedy", "drama"],
    )


@pytest.fixture
def int_multiple_prop():
    return PropType(
        name="scores", type="int", multiple=True, default=[], enumeration=None
    )


@pytest.fixture
def all_prop_types(
    str_prop,
    bool_prop,
    int_prop,
    float_prop,
    str_multiple_prop,
    enum_prop,
    enum_multiple_prop,
):
    return [
        str_prop,
        bool_prop,
        int_prop,
        float_prop,
        str_multiple_prop,
        enum_prop,
        enum_multiple_prop,
    ]


# -- NonSubmittingLineEdit --


class TestNonSubmittingLineEdit:
    def test_enter_emits_return_pressed(self, qtbot):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            NonSubmittingLineEdit,
        )

        widget = NonSubmittingLineEdit()
        qtbot.addWidget(widget)

        with qtbot.waitSignal(widget.returnPressed, timeout=1000):
            event = QKeyEvent(
                QKeyEvent.Type.KeyPress,
                Qt.Key.Key_Return,
                Qt.KeyboardModifier.NoModifier,
            )
            widget.keyPressEvent(event)

    def test_enter_key_is_accepted(self, qtbot):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            NonSubmittingLineEdit,
        )

        widget = NonSubmittingLineEdit()
        qtbot.addWidget(widget)

        event = QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier
        )
        widget.keyPressEvent(event)
        assert event.isAccepted()

    def test_other_keys_pass_through(self, qtbot):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            NonSubmittingLineEdit,
        )

        widget = NonSubmittingLineEdit()
        qtbot.addWidget(widget)

        widget.keyPressEvent(
            QKeyEvent(
                QKeyEvent.Type.KeyPress,
                Qt.Key.Key_A,
                Qt.KeyboardModifier.NoModifier,
                "a",
            )
        )
        assert widget.text() == "a"


# -- MultipleValuesWidget (free-form) --


class TestMultipleValuesWidgetFreeForm:
    def test_creation(self, qtbot, str_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(str_multiple_prop)
        qtbot.addWidget(w)

        assert hasattr(w, "list_widget")
        assert hasattr(w, "input_edit")
        assert w.list_widget.count() == 0

    def test_add_value(self, qtbot, str_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(str_multiple_prop)
        qtbot.addWidget(w)

        w.input_edit.setText("hello")
        w._add_value()

        assert w.list_widget.count() == 1
        assert w.input_edit.text() == ""

    def test_add_empty_value_ignored(self, qtbot, str_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(str_multiple_prop)
        qtbot.addWidget(w)

        w.input_edit.setText("   ")
        w._add_value()

        assert w.list_widget.count() == 0

    def test_add_duplicate_ignored(self, qtbot, str_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(str_multiple_prop)
        qtbot.addWidget(w)

        w.input_edit.setText("hello")
        w._add_value()
        w.input_edit.setText("hello")
        w._add_value()

        assert w.list_widget.count() == 1

    def test_get_values(self, qtbot, str_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(str_multiple_prop)
        qtbot.addWidget(w)

        w.input_edit.setText("a")
        w._add_value()
        w.input_edit.setText("b")
        w._add_value()

        assert w.get_values() == ["a", "b"]

    def test_remove_selected(self, qtbot, str_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(str_multiple_prop)
        qtbot.addWidget(w)

        w.input_edit.setText("a")
        w._add_value()
        w.input_edit.setText("b")
        w._add_value()

        # Select first item and remove
        w.list_widget.setCurrentRow(0)
        w._remove_selected()

        assert w.list_widget.count() == 1
        assert w.get_values() == ["b"]

    def test_clear_values(self, qtbot, str_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(str_multiple_prop)
        qtbot.addWidget(w)

        w.input_edit.setText("a")
        w._add_value()
        w.input_edit.setText("b")
        w._add_value()

        w._clear_values()

        assert w.list_widget.count() == 0

    def test_set_enabled(self, qtbot, str_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(str_multiple_prop)
        qtbot.addWidget(w)

        w.setEnabled(False)
        assert not w.list_widget.isEnabled()
        assert not w.input_edit.isEnabled()
        for btn in w._buttons:
            assert not btn.isEnabled()

        w.setEnabled(True)
        assert w.list_widget.isEnabled()
        assert w.input_edit.isEnabled()

    def test_add_int_value(self, qtbot, int_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(int_multiple_prop)
        qtbot.addWidget(w)

        w.input_edit.setText("42")
        w._add_value()

        assert w.get_values() == [42]

    def test_add_invalid_int_ignored(self, qtbot, int_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(int_multiple_prop)
        qtbot.addWidget(w)

        w.input_edit.setText("not_a_number")
        w._add_value()

        assert w.list_widget.count() == 0


# -- MultipleValuesWidget (enum) --


class TestMultipleValuesWidgetEnum:
    def test_creation(self, qtbot, enum_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(enum_multiple_prop)
        qtbot.addWidget(w)

        assert hasattr(w, "checkboxes")
        assert len(w.checkboxes) == 3

    def test_get_values_none_checked(self, qtbot, enum_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(enum_multiple_prop)
        qtbot.addWidget(w)

        assert w.get_values() == []

    def test_get_values_some_checked(self, qtbot, enum_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(enum_multiple_prop)
        qtbot.addWidget(w)

        w.checkboxes["action"].setChecked(True)
        w.checkboxes["drama"].setChecked(True)

        values = w.get_values()
        assert "action" in values
        assert "drama" in values
        assert "comedy" not in values

    def test_clear_values(self, qtbot, enum_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(enum_multiple_prop)
        qtbot.addWidget(w)

        w.checkboxes["action"].setChecked(True)
        w.checkboxes["comedy"].setChecked(True)
        w._clear_values()

        assert w.get_values() == []

    def test_set_enabled(self, qtbot, enum_multiple_prop):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            MultipleValuesWidget,
        )

        w = MultipleValuesWidget(enum_multiple_prop)
        qtbot.addWidget(w)

        w.setEnabled(False)
        for cb in w.checkboxes.values():
            assert not cb.isEnabled()

        w.setEnabled(True)
        for cb in w.checkboxes.values():
            assert cb.isEnabled()


# -- BatchEditDialog --


class TestBatchEditDialogCreation:
    def test_creation_with_props(self, qtbot, all_prop_types, mock_context):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1, 2, 3], all_prop_types, mock_context)
        qtbot.addWidget(dialog)

        assert "3 videos" in dialog.windowTitle()
        assert len(dialog._property_widgets) == len(all_prop_types)

    def test_creation_no_props(self, qtbot, mock_context):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [], mock_context)
        qtbot.addWidget(dialog)

        assert len(dialog._property_widgets) == 0

    def test_property_widgets_initially_disabled(
        self, qtbot, all_prop_types, mock_context
    ):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], all_prop_types, mock_context)
        qtbot.addWidget(dialog)

        for name, (checkbox, widget) in dialog._property_widgets.items():
            assert not checkbox.isChecked()
            assert not widget.isEnabled()


class TestBatchEditDialogPropertyGroups:
    def test_bool_property_creates_checkbox(self, qtbot, bool_prop, mock_context):
        from PySide6.QtWidgets import QCheckBox

        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [bool_prop], mock_context)
        qtbot.addWidget(dialog)

        _, widget = dialog._property_widgets["watched"]
        assert isinstance(widget, QCheckBox)

    def test_int_property_creates_spinbox(self, qtbot, int_prop, mock_context):
        from PySide6.QtWidgets import QSpinBox

        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [int_prop], mock_context)
        qtbot.addWidget(dialog)

        _, widget = dialog._property_widgets["rating"]
        assert isinstance(widget, QSpinBox)
        assert widget.value() == 0

    def test_float_property_creates_lineedit(self, qtbot, float_prop, mock_context):
        from PySide6.QtWidgets import QLineEdit

        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [float_prop], mock_context)
        qtbot.addWidget(dialog)

        _, widget = dialog._property_widgets["score"]
        assert isinstance(widget, QLineEdit)

    def test_str_property_creates_lineedit(self, qtbot, str_prop, mock_context):
        from PySide6.QtWidgets import QLineEdit

        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [str_prop], mock_context)
        qtbot.addWidget(dialog)

        _, widget = dialog._property_widgets["title"]
        assert isinstance(widget, QLineEdit)

    def test_enum_property_creates_combobox(self, qtbot, enum_prop, mock_context):
        from PySide6.QtWidgets import QComboBox

        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [enum_prop], mock_context)
        qtbot.addWidget(dialog)

        _, widget = dialog._property_widgets["status"]
        assert isinstance(widget, QComboBox)
        assert widget.count() == 3

    def test_multiple_property_creates_multiple_values_widget(
        self, qtbot, str_multiple_prop, mock_context
    ):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import (
            BatchEditDialog,
            MultipleValuesWidget,
        )

        dialog = BatchEditDialog([1], [str_multiple_prop], mock_context)
        qtbot.addWidget(dialog)

        _, widget = dialog._property_widgets["tags"]
        assert isinstance(widget, MultipleValuesWidget)

    def test_label_shows_multiple_indicator(
        self, qtbot, str_multiple_prop, mock_context
    ):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [str_multiple_prop], mock_context)
        qtbot.addWidget(dialog)

        checkbox, _ = dialog._property_widgets["tags"]
        assert "(multiple)" in checkbox.text()

    def test_label_shows_enum_indicator(self, qtbot, enum_multiple_prop, mock_context):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [enum_multiple_prop], mock_context)
        qtbot.addWidget(dialog)

        checkbox, _ = dialog._property_widgets["categories"]
        assert "[enum]" in checkbox.text()


class TestBatchEditDialogCheckboxToggle:
    def test_checking_enables_widget(self, qtbot, str_prop, mock_context):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [str_prop], mock_context)
        qtbot.addWidget(dialog)

        checkbox, widget = dialog._property_widgets["title"]
        assert not widget.isEnabled()

        checkbox.setChecked(True)
        assert widget.isEnabled()

    def test_unchecking_disables_widget(self, qtbot, str_prop, mock_context):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [str_prop], mock_context)
        qtbot.addWidget(dialog)

        checkbox, widget = dialog._property_widgets["title"]
        checkbox.setChecked(True)
        checkbox.setChecked(False)
        assert not widget.isEnabled()


class TestBatchEditDialogAccept:
    def test_accept_no_database(self, qtbot):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        class NoDbCtx:
            def has_database(self):
                return False

        dialog = BatchEditDialog([1], [], NoDbCtx())
        qtbot.addWidget(dialog)

        # Should not raise
        dialog._on_accept()

    def test_accept_no_changes(self, qtbot, str_prop, mock_context):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1, 2], [str_prop], mock_context)
        qtbot.addWidget(dialog)

        # No checkbox checked: no changes applied
        calls = []
        mock_context.set_video_properties = lambda vid, props: calls.append(
            (vid, props)
        )

        dialog._on_accept()
        assert calls == []

    def test_accept_applies_str_change(self, qtbot, str_prop, mock_context):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([10, 20], [str_prop], mock_context)
        qtbot.addWidget(dialog)

        checkbox, widget = dialog._property_widgets["title"]
        checkbox.setChecked(True)
        widget.setText("New Title")

        calls = []
        mock_context.set_video_properties = lambda vid, props: calls.append(
            (vid, props)
        )

        dialog._on_accept()

        assert len(calls) == 2
        assert calls[0] == (10, {"title": ["New Title"]})
        assert calls[1] == (20, {"title": ["New Title"]})

    def test_accept_applies_bool_change(self, qtbot, bool_prop, mock_context):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [bool_prop], mock_context)
        qtbot.addWidget(dialog)

        checkbox, widget = dialog._property_widgets["watched"]
        checkbox.setChecked(True)
        widget.setChecked(True)

        calls = []
        mock_context.set_video_properties = lambda vid, props: calls.append(
            (vid, props)
        )

        dialog._on_accept()

        assert len(calls) == 1
        assert calls[0] == (1, {"watched": [True]})

    def test_accept_applies_int_change(self, qtbot, int_prop, mock_context):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [int_prop], mock_context)
        qtbot.addWidget(dialog)

        checkbox, widget = dialog._property_widgets["rating"]
        checkbox.setChecked(True)
        widget.setValue(5)

        calls = []
        mock_context.set_video_properties = lambda vid, props: calls.append(
            (vid, props)
        )

        dialog._on_accept()

        assert len(calls) == 1
        assert calls[0] == (1, {"rating": [5]})

    def test_accept_applies_float_change(self, qtbot, float_prop, mock_context):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [float_prop], mock_context)
        qtbot.addWidget(dialog)

        checkbox, widget = dialog._property_widgets["score"]
        checkbox.setChecked(True)
        widget.setText("3.14")

        calls = []
        mock_context.set_video_properties = lambda vid, props: calls.append(
            (vid, props)
        )

        dialog._on_accept()

        assert len(calls) == 1
        assert calls[0] == (1, {"score": [3.14]})

    def test_accept_applies_enum_change(self, qtbot, enum_prop, mock_context):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [enum_prop], mock_context)
        qtbot.addWidget(dialog)

        checkbox, widget = dialog._property_widgets["status"]
        checkbox.setChecked(True)
        widget.setCurrentIndex(2)  # "archived"

        calls = []
        mock_context.set_video_properties = lambda vid, props: calls.append(
            (vid, props)
        )

        dialog._on_accept()

        assert len(calls) == 1
        assert calls[0] == (1, {"status": ["archived"]})

    def test_accept_applies_multiple_change(
        self, qtbot, str_multiple_prop, mock_context
    ):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [str_multiple_prop], mock_context)
        qtbot.addWidget(dialog)

        checkbox, widget = dialog._property_widgets["tags"]
        checkbox.setChecked(True)
        widget.input_edit.setText("tag1")
        widget._add_value()
        widget.input_edit.setText("tag2")
        widget._add_value()

        calls = []
        mock_context.set_video_properties = lambda vid, props: calls.append(
            (vid, props)
        )

        dialog._on_accept()

        assert len(calls) == 1
        assert calls[0] == (1, {"tags": ["tag1", "tag2"]})

    def test_accept_only_checked_properties(
        self, qtbot, str_prop, int_prop, mock_context
    ):
        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        dialog = BatchEditDialog([1], [str_prop, int_prop], mock_context)
        qtbot.addWidget(dialog)

        # Only check int
        cb_int, widget_int = dialog._property_widgets["rating"]
        cb_int.setChecked(True)
        widget_int.setValue(7)

        calls = []
        mock_context.set_video_properties = lambda vid, props: calls.append(
            (vid, props)
        )

        dialog._on_accept()

        assert len(calls) == 1
        assert "rating" in calls[0][1]
        assert "title" not in calls[0][1]
