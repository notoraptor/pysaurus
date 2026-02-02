"""
Tests for PySide6 PropertiesPage.

Tests the property management page.
"""

import pytest
from PySide6.QtCore import Qt


class TestPropertiesPageCreation:
    """Tests for PropertiesPage initialization."""

    def test_page_creation(self, qtbot, mock_context):
        """Test that PropertiesPage can be created."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        assert page.ctx == mock_context

    def test_page_has_table(self, qtbot, mock_context):
        """Test that page has properties table."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        assert page.props_table is not None
        assert page.props_table.columnCount() == 6

    def test_page_has_create_form(self, qtbot, mock_context):
        """Test that page has create property form."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        assert page.name_input is not None
        assert page.type_combo is not None
        assert page.multiple_check is not None
        assert page.btn_create is not None


class TestPropertiesPageRefresh:
    """Tests for refresh functionality."""

    def test_refresh_loads_properties(self, qtbot, mock_context):
        """Test that refresh loads properties from database."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        page.refresh()

        # Should have loaded properties (genre, rating from test data)
        assert page.props_table.rowCount() == 2

    def test_refresh_displays_property_info(self, qtbot, mock_context):
        """Test that refresh displays property information correctly."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        page.refresh()

        # Check first property (genre)
        name_item = page.props_table.item(0, 0)
        assert name_item is not None
        assert name_item.text() == "genre"


class TestPropertiesPageCreateForm:
    """Tests for the create property form."""

    def test_type_combo_has_options(self, qtbot, mock_context):
        """Test that type combo has all type options."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        options = [page.type_combo.itemText(i) for i in range(page.type_combo.count())]
        assert "str" in options
        assert "int" in options
        assert "float" in options
        assert "bool" in options

    def test_multiple_disabled_for_non_string(self, qtbot, mock_context):
        """Test that multiple checkbox is disabled for non-string types."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        # Select int type
        page.type_combo.setCurrentText("int")

        assert not page.multiple_check.isEnabled()
        assert not page.multiple_check.isChecked()

    def test_multiple_enabled_for_string(self, qtbot, mock_context):
        """Test that multiple checkbox is enabled for string type."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        # Select str type
        page.type_combo.setCurrentText("str")

        assert page.multiple_check.isEnabled()

    def test_enum_input_disabled_by_default(self, qtbot, mock_context):
        """Test that enum input is disabled by default."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        assert not page.enum_input.isEnabled()

    def test_enum_input_enabled_when_checked(self, qtbot, mock_context):
        """Test that enum input is enabled when checkbox is checked."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        page.enum_check.setChecked(True)

        assert page.enum_input.isEnabled()

    def test_reset_form(self, qtbot, mock_context):
        """Test that reset form clears all inputs."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        # Fill form
        page.name_input.setText("test_prop")
        page.type_combo.setCurrentText("int")
        page.default_input.setText("42")

        # Reset
        page._reset_form()

        assert page.name_input.text() == ""
        assert page.type_combo.currentText() == "str"
        assert page.default_input.text() == ""


class TestPropertiesPageCreate:
    """Tests for property creation."""

    def test_create_property_without_name_shows_warning(
        self, qtbot, mock_context, monkeypatch
    ):
        """Test that creating without name shows warning."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage
        from PySide6.QtWidgets import QMessageBox

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        warnings = []
        monkeypatch.setattr(
            QMessageBox, "warning", lambda *args, **kwargs: warnings.append(args)
        )

        page.btn_create.click()

        assert len(warnings) == 1
        assert "name" in warnings[0][2].lower()

    def test_create_property_success(self, qtbot, mock_context, monkeypatch):
        """Test successful property creation."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage
        from PySide6.QtWidgets import QMessageBox

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        # Mock QMessageBox.information
        infos = []
        monkeypatch.setattr(
            QMessageBox, "information", lambda *args, **kwargs: infos.append(args)
        )

        # Fill form
        page.name_input.setText("new_property")
        page.type_combo.setCurrentText("str")

        # Create
        page._on_create()

        # Should show success message
        assert len(infos) == 1
        assert "success" in infos[0][1].lower()

        # Property should be added to database
        prop_names = [pt["name"] for pt in mock_context.database.get_prop_types()]
        assert "new_property" in prop_names


class TestPropertiesPageActions:
    """Tests for property actions (rename, delete, convert)."""

    def test_delete_property(self, qtbot, mock_context, monkeypatch):
        """Test deleting a property."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage
        from PySide6.QtWidgets import QMessageBox

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Mock QMessageBox to auto-accept
        monkeypatch.setattr(
            QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        )

        initial_count = len(mock_context.database.get_prop_types())

        # Delete genre property
        page._on_delete("genre")

        assert len(mock_context.database.get_prop_types()) == initial_count - 1

    def test_rename_property(self, qtbot, mock_context, monkeypatch):
        """Test renaming a property."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage
        from PySide6.QtWidgets import QInputDialog, QMessageBox

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Mock QInputDialog to return new name
        monkeypatch.setattr(
            QInputDialog, "getText", lambda *args, **kwargs: ("new_genre", True)
        )
        # Mock QMessageBox.information
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

        # Rename genre property
        page._on_rename("genre")

        # Check that property was renamed
        prop_names = [pt["name"] for pt in mock_context.database.get_prop_types()]
        assert "new_genre" in prop_names
        assert "genre" not in prop_names

    def test_convert_property_multiplicity(self, qtbot, mock_context, monkeypatch):
        """Test converting property between single and multiple."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage
        from PySide6.QtWidgets import QMessageBox

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Mock QMessageBox to auto-accept
        monkeypatch.setattr(
            QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        )
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

        # Genre is multiple, convert to single
        page._on_convert("genre", True)

        # Check that property was converted
        prop_types = mock_context.database.get_prop_types()
        genre_prop = next(pt for pt in prop_types if pt["name"] == "genre")
        assert genre_prop["multiple"] is False
