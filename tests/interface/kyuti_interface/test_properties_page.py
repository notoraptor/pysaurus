"""
Tests for PySide6 PropertiesPage.

Tests the property management page.
"""

import pytest
from PySide6.QtWidgets import QInputDialog, QMessageBox

from pysaurus.interface.kyuti.pages.properties_page import PropertiesPage


class TestPropertiesPageCreation:
    """Tests for PropertiesPage initialization."""

    def test_page_creation(self, qtbot, mock_context):
        """Test that PropertiesPage can be created."""

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        assert page.ctx == mock_context

    def test_page_has_table(self, qtbot, mock_context):
        """Test that page has properties table."""

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        assert page.props_table is not None
        assert page.props_table.columnCount() == 6

    def test_page_has_create_form(self, qtbot, mock_context):
        """Test that page has create property form."""

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

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        page.refresh()

        # Should have loaded properties (genre, rating from test data)
        assert page.props_table.rowCount() == 2

    def test_refresh_displays_property_info(self, qtbot, mock_context):
        """Test that refresh displays property information correctly."""

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

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        options = [page.type_combo.itemText(i) for i in range(page.type_combo.count())]
        assert "str" in options
        assert "int" in options
        assert "float" in options
        assert "bool" in options

    def test_multiple_and_enum_disabled_for_bool(self, qtbot, mock_context):
        """Test that bool offers neither multiple values nor an enumeration."""

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        # Check them on a type that allows them, then switch to bool
        page.type_combo.setCurrentText("str")
        page.multiple_check.setChecked(True)
        page.enum_check.setChecked(True)

        page.type_combo.setCurrentText("bool")

        assert not page.multiple_check.isEnabled()
        assert not page.multiple_check.isChecked()
        assert not page.enum_check.isEnabled()
        assert not page.enum_check.isChecked()

    @pytest.mark.parametrize("type_name", ["str", "int", "float"])
    def test_multiple_and_enum_enabled_for_open_domain_types(
        self, qtbot, mock_context, type_name
    ):
        """Test that str, int and float all offer multiple and enumeration."""

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        page.type_combo.setCurrentText(type_name)

        assert page.multiple_check.isEnabled()
        assert page.enum_check.isEnabled()

    def test_default_field_disabled_when_unused(self, qtbot, mock_context):
        """Test that the default field is only editable when it is honoured."""

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        assert page.default_input.isEnabled()

        # A multiple property has no default value
        page.default_input.setText("42")
        page.multiple_check.setChecked(True)
        assert not page.default_input.isEnabled()
        assert page.default_input.text() == ""

        # An enumerated one takes its first enum value as default
        page.multiple_check.setChecked(False)
        assert page.default_input.isEnabled()
        page.enum_check.setChecked(True)
        assert not page.default_input.isEnabled()

        page.enum_check.setChecked(False)
        assert page.default_input.isEnabled()

    def test_bool_swaps_the_default_field_for_a_picker(self, qtbot, mock_context):
        """A bool default is picked out of its domain, not typed as text."""

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        assert page.default_input.isHidden() is False
        assert page.default_bool_input.isHidden() is True

        page.type_combo.setCurrentText("bool")

        assert page.default_input.isHidden() is True
        assert page.default_bool_input.isHidden() is False

        page.type_combo.setCurrentText("str")

        assert page.default_input.isHidden() is False
        assert page.default_bool_input.isHidden() is True

    @pytest.mark.parametrize("picked", [True, False])
    def test_bool_default_comes_from_the_picker_only(self, qtbot, mock_context, picked):
        """Regression: the default used to be parsed out of the text field.

        It matched the English literals "true"/"1"/"yes", so a French user
        typing "vrai" silently got False. The text field is now ignored.
        """

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        page.type_combo.setCurrentText("bool")
        page.default_bool_input.set_value(picked)
        page.default_input.setText("vrai")  # would have won before

        assert page._read_default("bool") is picked

    def test_enum_input_disabled_by_default(self, qtbot, mock_context):
        """Test that enum input is disabled by default."""

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        assert not page.enum_input.isEnabled()

    def test_enum_input_enabled_when_checked(self, qtbot, mock_context):
        """Test that enum input is enabled when checkbox is checked."""

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        page.enum_check.setChecked(True)

        assert page.enum_input.isEnabled()

    def test_reset_form(self, qtbot, mock_context):
        """Test that reset form clears all inputs."""

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
        prop_names = [pt.name for pt in mock_context.get_prop_types()]
        assert "new_property" in prop_names

    @pytest.mark.parametrize(
        "type_name,enum_text,expected",
        [
            ("int", "3, 1, 2", [3, 1, 2]),
            ("float", "1.5, 2.5", [1.5, 2.5]),
            ("str", " b , a ", ["b", "a"]),
            # Duplicates are dropped, keeping the first occurrence
            ("int", "1, 2, 1", [1, 2]),
        ],
    )
    def test_enum_field_is_parsed_to_property_type(
        self, qtbot, mock_context, type_name, enum_text, expected
    ):
        """Enum values reach the backend typed, in the order they were typed."""

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        page.type_combo.setCurrentText(type_name)
        page.enum_check.setChecked(True)
        page.enum_input.setText(enum_text)

        assert page._read_definition(type_name) == expected

    def test_create_multiple_enum_property_for_int(
        self, qtbot, mock_context, monkeypatch
    ):
        """An int property can be both multiple and enumerated."""

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

        page.name_input.setText("ratings")
        page.type_combo.setCurrentText("int")
        page.multiple_check.setChecked(True)
        page.enum_check.setChecked(True)
        page.enum_input.setText("1, 2, 3")

        page._on_create()

        (prop,) = [pt for pt in mock_context.get_prop_types() if pt.name == "ratings"]
        assert prop.type == "int"
        assert prop.multiple is True
        assert prop.enumeration == [1, 2, 3]

    @pytest.mark.parametrize(
        "type_name,enum_text",
        [
            ("int", "1, oops"),
            ("float", "1.5, oops"),
            ("int", "5"),  # a single value is not an enumeration
            ("str", "a, a"),  # neither is the same value twice
            ("str", "   "),  # nor an empty field
        ],
    )
    def test_create_enum_property_rejects_invalid_input(
        self, qtbot, mock_context, monkeypatch, type_name, enum_text
    ):
        """Untyped or too-short enumerations are refused with a warning."""

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)

        warnings = []
        monkeypatch.setattr(
            QMessageBox, "warning", lambda *args, **kwargs: warnings.append(args)
        )

        page.name_input.setText("bad_enum")
        page.type_combo.setCurrentText(type_name)
        page.enum_check.setChecked(True)
        page.enum_input.setText(enum_text)

        page._on_create()

        assert len(warnings) == 1
        assert not [pt for pt in mock_context.get_prop_types() if pt.name == "bad_enum"]

    @pytest.mark.parametrize("picked", [True, False])
    def test_create_bool_property_with_picked_default(
        self, qtbot, mock_context, monkeypatch, picked
    ):
        """The picked state reaches the backend as a real bool."""

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

        page.name_input.setText("watched")
        page.type_combo.setCurrentText("bool")
        page.default_bool_input.set_value(picked)

        page._on_create()

        (prop,) = [pt for pt in mock_context.get_prop_types() if pt.name == "watched"]
        assert prop.type == "bool"
        assert prop.multiple is False
        assert prop.enumeration is None  # never stored for a bool
        assert prop.default == [picked]


class TestPropertiesPageBoolColumns:
    """A bool has no stored enumeration, but the table still shows its domain."""

    @pytest.fixture
    def page_with_bool(self, qtbot, mock_context):
        mock_context.create_prop_type("watched", "bool", True, False)
        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()
        return page

    @staticmethod
    def _row_of(page, name: str) -> int:
        for row in range(page.props_table.rowCount()):
            if page.props_table.item(row, 0).text() == name:
                return row
        raise AssertionError(f"property not listed: {name}")

    def test_enum_column_shows_the_implicit_domain(self, page_with_bool):
        row = self._row_of(page_with_bool, "watched")
        assert page_with_bool.props_table.item(row, 4).text() == "false, true"

    def test_default_column_uses_the_literal_register(self, page_with_bool):
        """Not "True": the table lists a value, it does not ask a question."""
        row = self._row_of(page_with_bool, "watched")
        assert page_with_bool.props_table.item(row, 2).text() == "true"

    def test_unconstrained_property_still_shows_a_dash(self, page_with_bool):
        row = self._row_of(page_with_bool, "genre")
        assert page_with_bool.props_table.item(row, 4).text() == "-"


class TestPropertiesPageActions:
    """Tests for property actions (rename, delete, convert)."""

    def test_delete_property(self, qtbot, mock_context, monkeypatch):
        """Test deleting a property."""

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Mock QMessageBox to auto-accept
        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )

        initial_count = len(mock_context.get_prop_types())

        # Delete genre property
        page._on_delete("genre")

        assert len(mock_context.get_prop_types()) == initial_count - 1

    def test_rename_property(self, qtbot, mock_context, monkeypatch):
        """Test renaming a property."""

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
        prop_names = [pt.name for pt in mock_context.get_prop_types()]
        assert "new_genre" in prop_names
        assert "genre" not in prop_names

    def test_convert_property_multiplicity(self, qtbot, mock_context, monkeypatch):
        """Test converting property between single and multiple."""

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Mock QMessageBox to auto-accept
        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

        # Genre is multiple, convert to single
        page._on_convert("genre", True)

        # Check that property was converted
        prop_types = mock_context.get_prop_types()
        genre_prop = next(pt for pt in prop_types if pt.name == "genre")
        assert genre_prop.multiple is False
