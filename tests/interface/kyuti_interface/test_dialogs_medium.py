"""
Tests for PySide6 dialogs (medium priority).

Tests SortingDialog, GroupingDialog, SourcesDialog, GoToPageDialog.
"""

import pytest
from PySide6.QtWidgets import QComboBox, QDialogButtonBox, QPushButton

from pysaurus.interface.common.common import Uniconst
from pysaurus.interface.kyuti.dialogs.goto_page_dialog import GoToPageDialog
from pysaurus.interface.kyuti.dialogs.grouping_dialog import GroupingDialog
from pysaurus.interface.kyuti.dialogs.sorting_dialog import SortingDialog
from pysaurus.interface.kyuti.dialogs.sources_dialog import SourcesDialog
from pysaurus.properties.properties import PropType


class TestSortingDialog:
    """Tests for SortingDialog."""

    @staticmethod
    def _row_combo(dialog, row: int) -> QComboBox:
        """The field dropdown embedded in the criterion row at ``row``."""
        widget = dialog.sort_list.itemWidget(dialog.sort_list.item(row))
        return widget.findChild(QComboBox)

    @staticmethod
    def _row_button(dialog, row: int, texts: tuple[str, ...]) -> QPushButton:
        """A per-row button identified by its glyph, in the row at ``row``."""
        widget = dialog.sort_list.itemWidget(dialog.sort_list.item(row))
        return next(b for b in widget.findChildren(QPushButton) if b.text() in texts)

    def test_dialog_creation(self, qtbot):
        """Test that dialog can be created."""
        dialog = SortingDialog()
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Set Sorting"
        assert dialog.sort_list is not None

    def test_dialog_loads_current_sorting(self, qtbot):
        """Test that dialog loads current sorting."""
        current = [("title", False), ("date", True)]
        dialog = SortingDialog(current_sorting=current)
        qtbot.addWidget(dialog)

        assert dialog.sort_list.count() == 2
        assert dialog.get_sorting() == current

    def test_add_appends_ascending_row(self, qtbot):
        """Adding appends one ascending criterion on a real sortable field."""
        dialog = SortingDialog()
        qtbot.addWidget(dialog)

        initial_count = dialog.sort_list.count()
        dialog._on_add()

        assert dialog.sort_list.count() == initial_count + 1
        field, reverse = dialog.get_sorting()[-1]
        assert reverse is False
        assert field  # a concrete sortable field, not empty

    def test_change_field_via_dropdown(self, qtbot):
        """The point of the redesign: retarget a criterion without re-adding."""
        dialog = SortingDialog(current_sorting=[("title", False)])
        qtbot.addWidget(dialog)

        combo = self._row_combo(dialog, 0)
        combo.setCurrentIndex(combo.findData("length"))

        assert dialog.get_sorting() == [("length", False)]

    def test_toggle_direction(self, qtbot):
        """Test toggling sort direction."""
        dialog = SortingDialog(current_sorting=[("title", False)])
        qtbot.addWidget(dialog)

        dialog._toggle_direction(0)

        assert dialog.get_sorting() == [("title", True)]

    def test_row_buttons_survive_clicks(self, qtbot):
        # Each per-row button rebuilds the list synchronously, deleting the very
        # button that emitted the click; Qt guards clicked() so it must not crash.
        dialog = SortingDialog(current_sorting=[("title", False), ("date", True)])
        qtbot.addWidget(dialog)

        # Flip row 0's direction via its ▲/▼ button.
        self._row_button(dialog, 0, (Uniconst.ARROW_UP, Uniconst.ARROW_DOWN)).click()
        assert dialog.get_sorting() == [("title", True), ("date", True)]

        # Move row 1 up via its ↑ button.
        self._row_button(dialog, 1, ("↑",)).click()
        assert dialog.get_sorting() == [("date", True), ("title", True)]

        # Remove row 0 via its ✕ button.
        self._row_button(dialog, 0, (Uniconst.CROSS,)).click()
        assert dialog.get_sorting() == [("title", True)]

    def test_move_up(self, qtbot):
        """Test moving an item up."""
        dialog = SortingDialog(current_sorting=[("title", False), ("date", True)])
        qtbot.addWidget(dialog)

        dialog._move_up(1)

        assert dialog.get_sorting() == [("date", True), ("title", False)]

    def test_move_down(self, qtbot):
        """Test moving an item down."""
        dialog = SortingDialog(current_sorting=[("title", False), ("date", True)])
        qtbot.addWidget(dialog)

        dialog._move_down(0)

        assert dialog.get_sorting() == [("date", True), ("title", False)]

    def test_remove(self, qtbot):
        """Test removing a criterion by index."""
        dialog = SortingDialog(current_sorting=[("title", False), ("date", True)])
        qtbot.addWidget(dialog)

        dialog._remove(0)

        assert dialog.sort_list.count() == 1
        assert dialog.get_sorting() == [("date", True)]

    def test_unknown_field_preserved(self, qtbot):
        """A criterion on a non-sortable/removed field is kept, not dropped."""
        dialog = SortingDialog(current_sorting=[("mystery", True)])
        qtbot.addWidget(dialog)

        assert self._row_combo(dialog, 0).currentData() == "mystery"
        assert dialog.get_sorting() == [("mystery", True)]

    def test_reset_restores_default_sorting(self, qtbot):
        """Reset repopulates the default order (date modified, descending)."""
        dialog = SortingDialog(current_sorting=[("width", False), ("height", True)])
        qtbot.addWidget(dialog)

        reset_btn = next(
            b
            for b in dialog._button_box.buttons()
            if dialog._button_box.buttonRole(b) == QDialogButtonBox.ButtonRole.ResetRole
        )
        reset_btn.click()

        assert dialog.get_sorting() == [("date", True)]

    def test_get_sorting(self, qtbot):
        """Test getting sorting results."""
        current = [("title", False), ("date", True)]
        dialog = SortingDialog(current_sorting=current)
        qtbot.addWidget(dialog)

        assert dialog.get_sorting() == [("title", False), ("date", True)]


class TestGroupingDialog:
    """Tests for GroupingDialog."""

    @pytest.fixture
    def prop_types(self):
        """Sample property types."""
        return [
            PropType(
                name="genre", type="str", multiple=True, default=[], enumeration=None
            ),
            PropType(
                name="rating", type="int", multiple=False, default=[0], enumeration=None
            ),
        ]

    def test_dialog_creation(self, qtbot, prop_types):
        """Test that dialog can be created."""
        dialog = GroupingDialog(prop_types=prop_types)
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Set Grouping"

    def test_dialog_has_type_combo(self, qtbot, prop_types):
        """Test that dialog has type combo."""
        dialog = GroupingDialog(prop_types=prop_types)
        qtbot.addWidget(dialog)

        assert dialog.type_combo.count() == 2
        assert dialog.type_combo.itemText(0) == "Video Attribute"
        assert dialog.type_combo.itemText(1) == "Custom Property"

    def test_switch_to_property_type(self, qtbot, prop_types):
        """Test switching to property type populates properties."""
        dialog = GroupingDialog(prop_types=prop_types)
        qtbot.addWidget(dialog)

        # Switch to custom properties
        dialog.type_combo.setCurrentIndex(1)

        # Field combo should have property names
        fields = [
            dialog.field_combo.itemData(i) for i in range(dialog.field_combo.count())
        ]
        assert "genre" in fields
        assert "rating" in fields

    def test_sort_options(self, qtbot, prop_types):
        """Test sort options are available."""
        dialog = GroupingDialog(prop_types=prop_types)
        qtbot.addWidget(dialog)

        assert dialog.sort_field is not None
        assert dialog.sort_count is not None
        assert dialog.sort_length is not None

    def test_load_current_grouping(self, qtbot, prop_types):
        """Test loading current grouping."""
        current = {
            "field": "genre",
            "is_property": True,
            "sorting": "count",
            "reverse": True,
            "allow_singletons": False,
        }
        dialog = GroupingDialog(prop_types=prop_types, current_grouping=current)
        qtbot.addWidget(dialog)

        assert dialog.type_combo.currentIndex() == 1
        assert dialog.sort_count.isChecked()
        assert dialog.reverse_check.isChecked()
        assert not dialog.singletons_check.isChecked()

    def test_get_grouping(self, qtbot, prop_types):
        """Test getting grouping result."""
        dialog = GroupingDialog(prop_types=prop_types)
        qtbot.addWidget(dialog)

        # Set options
        dialog.type_combo.setCurrentIndex(1)  # Custom property
        dialog.sort_count.setChecked(True)
        dialog.reverse_check.setChecked(True)
        dialog.singletons_check.setChecked(False)

        result = dialog.get_grouping()

        assert result["is_property"] is True
        assert result["sorting"] == "count"
        assert result["reverse"] is True
        assert result["allow_singletons"] is False


class TestSourcesDialog:
    """Tests for SourcesDialog."""

    def test_dialog_creation(self, qtbot):
        """Test that dialog can be created."""
        dialog = SourcesDialog()
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Select Sources"

    def test_dialog_has_checkboxes(self, qtbot):
        """Test that dialog has all source checkboxes."""
        dialog = SourcesDialog()
        qtbot.addWidget(dialog)

        # Should have 6 checkboxes
        assert len(dialog._checkboxes) == 6
        assert "readable.found.with_thumbnails" in dialog._checkboxes
        assert "readable.found.without_thumbnails" in dialog._checkboxes
        assert "readable.not_found.with_thumbnails" in dialog._checkboxes
        assert "readable.not_found.without_thumbnails" in dialog._checkboxes
        assert "unreadable.found" in dialog._checkboxes
        assert "unreadable.not_found" in dialog._checkboxes

    def test_select_all(self, qtbot):
        """Test selecting all sources."""
        dialog = SourcesDialog()
        qtbot.addWidget(dialog)

        dialog._select_all()

        for cb in dialog._checkboxes.values():
            assert cb.isChecked()

    def test_select_none(self, qtbot):
        """Test deselecting all sources."""
        dialog = SourcesDialog()
        qtbot.addWidget(dialog)

        dialog._select_all()
        dialog._select_none()

        for cb in dialog._checkboxes.values():
            assert not cb.isChecked()

    def test_select_valid(self, qtbot):
        """Test selecting only valid sources."""
        dialog = SourcesDialog()
        qtbot.addWidget(dialog)

        dialog._select_valid()

        # Only readable.found.with_thumbnails should be checked
        assert dialog._checkboxes["readable.found.with_thumbnails"].isChecked()
        assert not dialog._checkboxes["readable.found.without_thumbnails"].isChecked()
        assert not dialog._checkboxes["unreadable.found"].isChecked()

    def test_load_current_sources(self, qtbot):
        """Test loading current sources."""
        current = [["readable", "found", "with_thumbnails"], ["unreadable", "found"]]
        dialog = SourcesDialog(current_sources=current)
        qtbot.addWidget(dialog)

        assert dialog._checkboxes["readable.found.with_thumbnails"].isChecked()
        assert dialog._checkboxes["unreadable.found"].isChecked()
        assert not dialog._checkboxes["readable.not_found.with_thumbnails"].isChecked()

    def test_get_sources(self, qtbot):
        """Test getting selected sources."""
        dialog = SourcesDialog()
        qtbot.addWidget(dialog)

        dialog._select_none()
        dialog._checkboxes["readable.found.with_thumbnails"].setChecked(True)
        dialog._checkboxes["unreadable.found"].setChecked(True)

        sources = dialog.get_sources()

        assert ["readable", "found", "with_thumbnails"] in sources
        assert ["unreadable", "found"] in sources
        assert len(sources) == 2


class TestGoToPageDialog:
    """Tests for GoToPageDialog."""

    def test_dialog_creation(self, qtbot):
        """Test that dialog can be created."""
        dialog = GoToPageDialog(current_page=1, total_pages=10)
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Go to Page"

    def test_dialog_shows_current_page(self, qtbot):
        """Test that dialog shows current page."""
        dialog = GoToPageDialog(current_page=5, total_pages=10)
        qtbot.addWidget(dialog)

        assert dialog.page_spin.value() == 5

    def test_dialog_limits_to_total_pages(self, qtbot):
        """Test that spin box is limited to total pages."""
        dialog = GoToPageDialog(current_page=1, total_pages=10)
        qtbot.addWidget(dialog)

        assert dialog.page_spin.minimum() == 1
        assert dialog.page_spin.maximum() == 10

    def test_get_page_returns_zero_based(self, qtbot):
        """Test that get_page returns 0-based page number."""
        dialog = GoToPageDialog(current_page=5, total_pages=10)
        qtbot.addWidget(dialog)

        dialog.page_spin.setValue(7)

        # Page 7 (1-based) should be 6 (0-based)
        assert dialog.get_page() == 6

    def test_get_page_first_page(self, qtbot):
        """Test getting first page."""
        dialog = GoToPageDialog(current_page=1, total_pages=10)
        qtbot.addWidget(dialog)

        dialog.page_spin.setValue(1)

        assert dialog.get_page() == 0

    def test_get_page_last_page(self, qtbot):
        """Test getting last page."""
        dialog = GoToPageDialog(current_page=1, total_pages=10)
        qtbot.addWidget(dialog)

        dialog.page_spin.setValue(10)

        assert dialog.get_page() == 9

    def test_dialog_handles_single_page(self, qtbot):
        """Test dialog with only one page."""
        dialog = GoToPageDialog(current_page=1, total_pages=1)
        qtbot.addWidget(dialog)

        assert dialog.page_spin.minimum() == 1
        assert dialog.page_spin.maximum() == 1
        assert dialog.get_page() == 0
