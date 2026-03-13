"""
Tests for FillPropertyDialog.

Tests the dialog for filling a property with terms extracted from video titles.
"""

import pytest
from PySide6.QtWidgets import QDialogButtonBox

from pysaurus.properties.properties import PropType


@pytest.fixture
def str_multiple_prop():
    return PropType(
        name="tags", type="str", multiple=True, default=[], enumeration=None
    )


@pytest.fixture
def str_single_prop():
    return PropType(
        name="title", type="str", multiple=False, default=[""], enumeration=None
    )


@pytest.fixture
def int_prop():
    return PropType(
        name="rating", type="int", multiple=False, default=[0], enumeration=None
    )


@pytest.fixture
def mixed_prop_types(str_multiple_prop, str_single_prop, int_prop):
    return [str_multiple_prop, str_single_prop, int_prop]


@pytest.fixture
def two_eligible_props():
    return [
        PropType(name="tags", type="str", multiple=True, default=[], enumeration=None),
        PropType(
            name="keywords", type="str", multiple=True, default=[], enumeration=None
        ),
    ]


class TestFillPropertyDialogCreation:
    def test_creation(self, qtbot, mixed_prop_types):
        from pysaurus.interface.pyside6.dialogs.fill_property_dialog import (
            FillPropertyDialog,
        )

        dialog = FillPropertyDialog(mixed_prop_types)
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Fill Property with Terms"

    def test_filters_eligible_properties(self, qtbot, mixed_prop_types):
        from pysaurus.interface.pyside6.dialogs.fill_property_dialog import (
            FillPropertyDialog,
        )

        dialog = FillPropertyDialog(mixed_prop_types)
        qtbot.addWidget(dialog)

        # Only str+multiple should be eligible (tags)
        assert len(dialog._eligible_props) == 1
        assert dialog._eligible_props[0].name == "tags"

    def test_combo_shows_eligible_props(self, qtbot, two_eligible_props):
        from pysaurus.interface.pyside6.dialogs.fill_property_dialog import (
            FillPropertyDialog,
        )

        dialog = FillPropertyDialog(two_eligible_props)
        qtbot.addWidget(dialog)

        assert dialog.prop_combo.count() == 2
        assert dialog.prop_combo.itemText(0) == "tags"
        assert dialog.prop_combo.itemText(1) == "keywords"

    def test_combo_disabled_when_no_eligible(self, qtbot, int_prop):
        from pysaurus.interface.pyside6.dialogs.fill_property_dialog import (
            FillPropertyDialog,
        )

        dialog = FillPropertyDialog([int_prop])
        qtbot.addWidget(dialog)

        assert not dialog.prop_combo.isEnabled()

    def test_ok_disabled_when_no_eligible(self, qtbot, int_prop):
        from pysaurus.interface.pyside6.dialogs.fill_property_dialog import (
            FillPropertyDialog,
        )

        dialog = FillPropertyDialog([int_prop])
        qtbot.addWidget(dialog)

        button_box = dialog.findChild(QDialogButtonBox)
        ok_btn = button_box.button(QDialogButtonBox.StandardButton.Ok)
        assert not ok_btn.isEnabled()

    def test_only_empty_initially_unchecked(self, qtbot, mixed_prop_types):
        from pysaurus.interface.pyside6.dialogs.fill_property_dialog import (
            FillPropertyDialog,
        )

        dialog = FillPropertyDialog(mixed_prop_types)
        qtbot.addWidget(dialog)

        assert not dialog.only_empty_check.isChecked()


class TestFillPropertyDialogAccept:
    def test_accept_returns_selected_prop(self, qtbot, two_eligible_props):
        from pysaurus.interface.pyside6.dialogs.fill_property_dialog import (
            FillPropertyDialog,
        )

        dialog = FillPropertyDialog(two_eligible_props)
        qtbot.addWidget(dialog)

        dialog.prop_combo.setCurrentIndex(1)  # keywords
        dialog._on_accept()

        prop, only_empty = dialog.get_result()
        assert prop.name == "keywords"
        assert only_empty is False

    def test_accept_with_only_empty(self, qtbot, two_eligible_props):
        from pysaurus.interface.pyside6.dialogs.fill_property_dialog import (
            FillPropertyDialog,
        )

        dialog = FillPropertyDialog(two_eligible_props)
        qtbot.addWidget(dialog)

        dialog.only_empty_check.setChecked(True)
        dialog._on_accept()

        prop, only_empty = dialog.get_result()
        assert only_empty is True

    def test_get_result_before_accept(self, qtbot, mixed_prop_types):
        from pysaurus.interface.pyside6.dialogs.fill_property_dialog import (
            FillPropertyDialog,
        )

        dialog = FillPropertyDialog(mixed_prop_types)
        qtbot.addWidget(dialog)

        prop, only_empty = dialog.get_result()
        assert prop is None
        assert only_empty is False

    def test_accept_no_eligible(self, qtbot, int_prop):
        from pysaurus.interface.pyside6.dialogs.fill_property_dialog import (
            FillPropertyDialog,
        )

        dialog = FillPropertyDialog([int_prop])
        qtbot.addWidget(dialog)

        dialog._on_accept()

        prop, only_empty = dialog.get_result()
        assert prop is None
