"""
Tests for MoveValuesDialog.

Tests the dialog for moving property values between properties.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialogButtonBox

from pysaurus.properties.properties import PropType


@pytest.fixture
def source_prop():
    return PropType(
        name="tags", type="str", multiple=True, default=[], enumeration=None
    )


@pytest.fixture
def target_str_single():
    return PropType(
        name="title", type="str", multiple=False, default=[""], enumeration=None
    )


@pytest.fixture
def target_str_multiple():
    return PropType(
        name="keywords", type="str", multiple=True, default=[], enumeration=None
    )


@pytest.fixture
def int_prop():
    return PropType(
        name="rating", type="int", multiple=False, default=[0], enumeration=None
    )


@pytest.fixture
def all_props(source_prop, target_str_single, target_str_multiple, int_prop):
    return [source_prop, target_str_single, target_str_multiple, int_prop]


class TestMoveValuesDialogCreation:
    def test_creation(self, qtbot, source_prop, all_props, mock_context):
        from pysaurus.interface.pyside6.dialogs.move_values_dialog import (
            MoveValuesDialog,
        )

        dialog = MoveValuesDialog(source_prop, all_props, mock_context)
        qtbot.addWidget(dialog)

        assert "tags" in dialog.windowTitle()

    def test_filters_target_properties(
        self, qtbot, source_prop, all_props, mock_context
    ):
        from pysaurus.interface.pyside6.dialogs.move_values_dialog import (
            MoveValuesDialog,
        )

        dialog = MoveValuesDialog(source_prop, all_props, mock_context)
        qtbot.addWidget(dialog)

        # Targets: str type, different from source
        # title (str single) and keywords (str multiple) qualify
        # rating (int) and tags (source) excluded
        assert len(dialog._target_props) == 2

    def test_target_combo_populated(self, qtbot, source_prop, all_props, mock_context):
        from pysaurus.interface.pyside6.dialogs.move_values_dialog import (
            MoveValuesDialog,
        )

        dialog = MoveValuesDialog(source_prop, all_props, mock_context)
        qtbot.addWidget(dialog)

        assert dialog.target_combo.count() == 2

    def test_no_targets_disables_ok(self, qtbot, source_prop, mock_context):
        from pysaurus.interface.pyside6.dialogs.move_values_dialog import (
            MoveValuesDialog,
        )

        # Only source and an int prop: no eligible targets
        props = [
            source_prop,
            PropType(
                name="rating", type="int", multiple=False, default=[0], enumeration=None
            ),
        ]
        dialog = MoveValuesDialog(source_prop, props, mock_context)
        qtbot.addWidget(dialog)

        button_box = dialog.findChild(QDialogButtonBox)
        ok_btn = button_box.button(QDialogButtonBox.StandardButton.Ok)
        assert not ok_btn.isEnabled()

    def test_no_targets_disables_combo(self, qtbot, source_prop, mock_context):
        from pysaurus.interface.pyside6.dialogs.move_values_dialog import (
            MoveValuesDialog,
        )

        props = [source_prop]  # Only source, no targets
        dialog = MoveValuesDialog(source_prop, props, mock_context)
        qtbot.addWidget(dialog)

        assert not dialog.target_combo.isEnabled()


class TestMoveValuesDialogValues:
    def test_loads_values_from_context(
        self, qtbot, source_prop, all_props, mock_context
    ):
        from pysaurus.interface.pyside6.dialogs.move_values_dialog import (
            MoveValuesDialog,
        )

        # Mock property values
        mock_context.get_property_values = lambda prop_name: {
            1: ["action", "comedy"],
            2: ["action", "drama"],
        }

        dialog = MoveValuesDialog(source_prop, all_props, mock_context)
        qtbot.addWidget(dialog)

        # Should have 3 unique values: action, comedy, drama
        assert dialog.values_list.count() == 3

    def test_values_sorted_by_count(self, qtbot, source_prop, all_props, mock_context):
        from pysaurus.interface.pyside6.dialogs.move_values_dialog import (
            MoveValuesDialog,
        )

        mock_context.get_property_values = lambda prop_name: {
            1: ["action", "comedy"],
            2: ["action", "drama"],
            3: ["action"],
        }

        dialog = MoveValuesDialog(source_prop, all_props, mock_context)
        qtbot.addWidget(dialog)

        # action (3), comedy (1), drama (1) — action should be first
        first_item = dialog.values_list.item(0)
        first_value = first_item.data(Qt.ItemDataRole.UserRole)
        assert first_value == "action"

    def test_empty_values(self, qtbot, source_prop, all_props, mock_context):
        from pysaurus.interface.pyside6.dialogs.move_values_dialog import (
            MoveValuesDialog,
        )

        mock_context.get_property_values = lambda prop_name: {}

        dialog = MoveValuesDialog(source_prop, all_props, mock_context)
        qtbot.addWidget(dialog)

        assert dialog.values_list.count() == 0


class TestMoveValuesDialogAccept:
    def test_accept_no_selection_shows_warning(
        self, qtbot, source_prop, all_props, mock_context, monkeypatch
    ):
        from pysaurus.interface.pyside6.dialogs.move_values_dialog import (
            MoveValuesDialog,
        )

        mock_context.get_property_values = lambda prop_name: {1: ["action"]}

        dialog = MoveValuesDialog(source_prop, all_props, mock_context)
        qtbot.addWidget(dialog)

        # Stub QMessageBox.warning to prevent blocking
        from PySide6.QtWidgets import QMessageBox

        warned = []
        monkeypatch.setattr(QMessageBox, "warning", lambda *args: warned.append(True))

        dialog._on_accept()

        assert len(warned) == 1

    def test_accept_with_selection(self, qtbot, source_prop, all_props, mock_context):
        from pysaurus.interface.pyside6.dialogs.move_values_dialog import (
            MoveValuesDialog,
        )

        mock_context.get_property_values = lambda prop_name: {1: ["action", "comedy"]}

        dialog = MoveValuesDialog(source_prop, all_props, mock_context)
        qtbot.addWidget(dialog)

        # Select first item
        dialog.values_list.setCurrentRow(0)

        dialog._on_accept()

        values, target_prop, concatenate = dialog.get_result()
        assert len(values) == 1
        assert target_prop is not None
        assert concatenate is False

    def test_accept_with_concatenate(self, qtbot, source_prop, all_props, mock_context):
        from pysaurus.interface.pyside6.dialogs.move_values_dialog import (
            MoveValuesDialog,
        )

        mock_context.get_property_values = lambda prop_name: {1: ["action", "comedy"]}

        dialog = MoveValuesDialog(source_prop, all_props, mock_context)
        qtbot.addWidget(dialog)

        dialog.values_list.selectAll()
        dialog.concatenate_check.setChecked(True)

        dialog._on_accept()

        values, target_prop, concatenate = dialog.get_result()
        assert len(values) == 2
        assert concatenate is True

    def test_get_result_before_accept(
        self, qtbot, source_prop, all_props, mock_context
    ):
        from pysaurus.interface.pyside6.dialogs.move_values_dialog import (
            MoveValuesDialog,
        )

        mock_context.get_property_values = lambda prop_name: {}

        dialog = MoveValuesDialog(source_prop, all_props, mock_context)
        qtbot.addWidget(dialog)

        values, target_prop, concatenate = dialog.get_result()
        assert values == []
        assert target_prop is None
        assert concatenate is False
