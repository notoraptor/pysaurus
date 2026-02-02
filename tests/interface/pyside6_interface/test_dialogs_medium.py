"""
Tests for PySide6 dialogs (medium priority).

Tests SortingDialog, GroupingDialog, SourcesDialog, GoToPageDialog.
"""

import pytest
from PySide6.QtCore import Qt


class TestSortingDialog:
    """Tests for SortingDialog."""

    def test_dialog_creation(self, qtbot):
        """Test that dialog can be created."""
        from pysaurus.interface.pyside6.dialogs.sorting_dialog import SortingDialog

        dialog = SortingDialog()
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Set Sorting"
        assert dialog.sort_list is not None

    def test_dialog_loads_current_sorting(self, qtbot):
        """Test that dialog loads current sorting."""
        from pysaurus.interface.pyside6.dialogs.sorting_dialog import SortingDialog

        current = [("title", False), ("date", True)]
        dialog = SortingDialog(current_sorting=current)
        qtbot.addWidget(dialog)

        # Should have 2 items in the list
        assert dialog.sort_list.count() == 2

    def test_add_field_ascending(self, qtbot):
        """Test adding a field with ascending order."""
        from pysaurus.interface.pyside6.dialogs.sorting_dialog import SortingDialog

        dialog = SortingDialog()
        qtbot.addWidget(dialog)

        initial_count = dialog.sort_list.count()

        # Add a field ascending
        dialog._add_field(False)

        assert dialog.sort_list.count() == initial_count + 1

    def test_add_field_descending(self, qtbot):
        """Test adding a field with descending order."""
        from pysaurus.interface.pyside6.dialogs.sorting_dialog import SortingDialog

        dialog = SortingDialog()
        qtbot.addWidget(dialog)

        # Add a field descending
        dialog._add_field(True)

        # Check the item has descending direction
        item = dialog.sort_list.item(dialog.sort_list.count() - 1)
        field, reverse = item.data(Qt.ItemDataRole.UserRole)
        assert reverse is True

    def test_move_up(self, qtbot):
        """Test moving an item up."""
        from pysaurus.interface.pyside6.dialogs.sorting_dialog import SortingDialog

        current = [("title", False), ("date", True)]
        dialog = SortingDialog(current_sorting=current)
        qtbot.addWidget(dialog)

        # Select second item
        dialog.sort_list.setCurrentRow(1)

        # Move up
        dialog._move_up()

        # Now it should be at position 0
        assert dialog.sort_list.currentRow() == 0
        item = dialog.sort_list.item(0)
        field, _ = item.data(Qt.ItemDataRole.UserRole)
        assert field == "date"

    def test_move_down(self, qtbot):
        """Test moving an item down."""
        from pysaurus.interface.pyside6.dialogs.sorting_dialog import SortingDialog

        current = [("title", False), ("date", True)]
        dialog = SortingDialog(current_sorting=current)
        qtbot.addWidget(dialog)

        # Select first item
        dialog.sort_list.setCurrentRow(0)

        # Move down
        dialog._move_down()

        # Now it should be at position 1
        assert dialog.sort_list.currentRow() == 1
        item = dialog.sort_list.item(1)
        field, _ = item.data(Qt.ItemDataRole.UserRole)
        assert field == "title"

    def test_toggle_direction(self, qtbot):
        """Test toggling sort direction."""
        from pysaurus.interface.pyside6.dialogs.sorting_dialog import SortingDialog

        current = [("title", False)]  # ascending
        dialog = SortingDialog(current_sorting=current)
        qtbot.addWidget(dialog)

        # Select item
        dialog.sort_list.setCurrentRow(0)

        # Toggle direction
        dialog._toggle_direction()

        # Check it's now descending
        item = dialog.sort_list.item(0)
        _, reverse = item.data(Qt.ItemDataRole.UserRole)
        assert reverse is True

    def test_remove_selected(self, qtbot):
        """Test removing selected item."""
        from pysaurus.interface.pyside6.dialogs.sorting_dialog import SortingDialog

        current = [("title", False), ("date", True)]
        dialog = SortingDialog(current_sorting=current)
        qtbot.addWidget(dialog)

        # Select first item
        dialog.sort_list.setCurrentRow(0)

        # Remove
        dialog._remove_selected()

        assert dialog.sort_list.count() == 1

    def test_get_sorting(self, qtbot):
        """Test getting sorting results."""
        from pysaurus.interface.pyside6.dialogs.sorting_dialog import SortingDialog

        current = [("title", False), ("date", True)]
        dialog = SortingDialog(current_sorting=current)
        qtbot.addWidget(dialog)

        result = dialog.get_sorting()

        # get_sorting() returns lists, not tuples
        expected = [["title", False], ["date", True]]
        assert result == expected


class TestGroupingDialog:
    """Tests for GroupingDialog."""

    @pytest.fixture
    def prop_types(self):
        """Sample property types."""
        return [
            {"name": "genre", "type": "str", "multiple": True},
            {"name": "rating", "type": "int", "multiple": False},
        ]

    def test_dialog_creation(self, qtbot, prop_types):
        """Test that dialog can be created."""
        from pysaurus.interface.pyside6.dialogs.grouping_dialog import GroupingDialog

        dialog = GroupingDialog(prop_types=prop_types)
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Set Grouping"

    def test_dialog_has_type_combo(self, qtbot, prop_types):
        """Test that dialog has type combo."""
        from pysaurus.interface.pyside6.dialogs.grouping_dialog import GroupingDialog

        dialog = GroupingDialog(prop_types=prop_types)
        qtbot.addWidget(dialog)

        assert dialog.type_combo.count() == 2
        assert dialog.type_combo.itemText(0) == "Video Attribute"
        assert dialog.type_combo.itemText(1) == "Custom Property"

    def test_switch_to_property_type(self, qtbot, prop_types):
        """Test switching to property type populates properties."""
        from pysaurus.interface.pyside6.dialogs.grouping_dialog import GroupingDialog

        dialog = GroupingDialog(prop_types=prop_types)
        qtbot.addWidget(dialog)

        # Switch to custom properties
        dialog.type_combo.setCurrentIndex(1)

        # Field combo should have property names
        fields = [dialog.field_combo.itemData(i) for i in range(dialog.field_combo.count())]
        assert "genre" in fields
        assert "rating" in fields

    def test_sort_options(self, qtbot, prop_types):
        """Test sort options are available."""
        from pysaurus.interface.pyside6.dialogs.grouping_dialog import GroupingDialog

        dialog = GroupingDialog(prop_types=prop_types)
        qtbot.addWidget(dialog)

        assert dialog.sort_field is not None
        assert dialog.sort_count is not None
        assert dialog.sort_length is not None

    def test_load_current_grouping(self, qtbot, prop_types):
        """Test loading current grouping."""
        from pysaurus.interface.pyside6.dialogs.grouping_dialog import GroupingDialog

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
        from pysaurus.interface.pyside6.dialogs.grouping_dialog import GroupingDialog

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
        from pysaurus.interface.pyside6.dialogs.sources_dialog import SourcesDialog

        dialog = SourcesDialog()
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Select Sources"

    def test_dialog_has_checkboxes(self, qtbot):
        """Test that dialog has all source checkboxes."""
        from pysaurus.interface.pyside6.dialogs.sources_dialog import SourcesDialog

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
        from pysaurus.interface.pyside6.dialogs.sources_dialog import SourcesDialog

        dialog = SourcesDialog()
        qtbot.addWidget(dialog)

        dialog._select_all()

        for cb in dialog._checkboxes.values():
            assert cb.isChecked()

    def test_select_none(self, qtbot):
        """Test deselecting all sources."""
        from pysaurus.interface.pyside6.dialogs.sources_dialog import SourcesDialog

        dialog = SourcesDialog()
        qtbot.addWidget(dialog)

        dialog._select_all()
        dialog._select_none()

        for cb in dialog._checkboxes.values():
            assert not cb.isChecked()

    def test_select_valid(self, qtbot):
        """Test selecting only valid sources."""
        from pysaurus.interface.pyside6.dialogs.sources_dialog import SourcesDialog

        dialog = SourcesDialog()
        qtbot.addWidget(dialog)

        dialog._select_valid()

        # Only readable.found.with_thumbnails should be checked
        assert dialog._checkboxes["readable.found.with_thumbnails"].isChecked()
        assert not dialog._checkboxes["readable.found.without_thumbnails"].isChecked()
        assert not dialog._checkboxes["unreadable.found"].isChecked()

    def test_load_current_sources(self, qtbot):
        """Test loading current sources."""
        from pysaurus.interface.pyside6.dialogs.sources_dialog import SourcesDialog

        current = [["readable", "found", "with_thumbnails"], ["unreadable", "found"]]
        dialog = SourcesDialog(current_sources=current)
        qtbot.addWidget(dialog)

        assert dialog._checkboxes["readable.found.with_thumbnails"].isChecked()
        assert dialog._checkboxes["unreadable.found"].isChecked()
        assert not dialog._checkboxes["readable.not_found.with_thumbnails"].isChecked()

    def test_get_sources(self, qtbot):
        """Test getting selected sources."""
        from pysaurus.interface.pyside6.dialogs.sources_dialog import SourcesDialog

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
        from pysaurus.interface.pyside6.dialogs.goto_page_dialog import GoToPageDialog

        dialog = GoToPageDialog(current_page=1, total_pages=10)
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Go to Page"

    def test_dialog_shows_current_page(self, qtbot):
        """Test that dialog shows current page."""
        from pysaurus.interface.pyside6.dialogs.goto_page_dialog import GoToPageDialog

        dialog = GoToPageDialog(current_page=5, total_pages=10)
        qtbot.addWidget(dialog)

        assert dialog.page_spin.value() == 5

    def test_dialog_limits_to_total_pages(self, qtbot):
        """Test that spin box is limited to total pages."""
        from pysaurus.interface.pyside6.dialogs.goto_page_dialog import GoToPageDialog

        dialog = GoToPageDialog(current_page=1, total_pages=10)
        qtbot.addWidget(dialog)

        assert dialog.page_spin.minimum() == 1
        assert dialog.page_spin.maximum() == 10

    def test_get_page_returns_zero_based(self, qtbot):
        """Test that get_page returns 0-based page number."""
        from pysaurus.interface.pyside6.dialogs.goto_page_dialog import GoToPageDialog

        dialog = GoToPageDialog(current_page=5, total_pages=10)
        qtbot.addWidget(dialog)

        dialog.page_spin.setValue(7)

        # Page 7 (1-based) should be 6 (0-based)
        assert dialog.get_page() == 6

    def test_get_page_first_page(self, qtbot):
        """Test getting first page."""
        from pysaurus.interface.pyside6.dialogs.goto_page_dialog import GoToPageDialog

        dialog = GoToPageDialog(current_page=1, total_pages=10)
        qtbot.addWidget(dialog)

        dialog.page_spin.setValue(1)

        assert dialog.get_page() == 0

    def test_get_page_last_page(self, qtbot):
        """Test getting last page."""
        from pysaurus.interface.pyside6.dialogs.goto_page_dialog import GoToPageDialog

        dialog = GoToPageDialog(current_page=1, total_pages=10)
        qtbot.addWidget(dialog)

        dialog.page_spin.setValue(10)

        assert dialog.get_page() == 9

    def test_dialog_handles_single_page(self, qtbot):
        """Test dialog with only one page."""
        from pysaurus.interface.pyside6.dialogs.goto_page_dialog import GoToPageDialog

        dialog = GoToPageDialog(current_page=1, total_pages=1)
        qtbot.addWidget(dialog)

        assert dialog.page_spin.minimum() == 1
        assert dialog.page_spin.maximum() == 1
        assert dialog.get_page() == 0
