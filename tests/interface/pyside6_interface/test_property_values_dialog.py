"""
Tests for PropertyValuesDialog in PySide6 interface.

Tests the full flow: PropertiesPage → PropertyValuesDialog → modifiers/actions,
verifying that property values are actually modified in the database and that
the dialog display reflects the changes.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox


class TestPropertyValuesDialogCreation:
    """Tests for dialog creation and initial display."""

    def test_dialog_creation(self, qtbot, mock_context):
        """Test that PropertyValuesDialog can be created."""
        from pysaurus.interface.pyside6.dialogs.property_values_dialog import (
            PropertyValuesDialog,
        )

        prop_types = mock_context.get_prop_types()
        genre_prop = next(pt for pt in prop_types if pt["name"] == "genre")

        dialog = PropertyValuesDialog("genre", genre_prop, mock_context)
        qtbot.addWidget(dialog)

        assert dialog.prop_name == "genre"

    def test_dialog_loads_values(self, qtbot, mock_context):
        """Test that dialog loads all property values with counts."""
        from pysaurus.interface.pyside6.dialogs.property_values_dialog import (
            PropertyValuesDialog,
        )

        prop_types = mock_context.get_prop_types()
        genre_prop = next(pt for pt in prop_types if pt["name"] == "genre")

        dialog = PropertyValuesDialog("genre", genre_prop, mock_context)
        qtbot.addWidget(dialog)

        # genre has: action(2), comedy(2), drama(1), romance(1)
        assert dialog.values_list.count() == 4

    def test_dialog_shows_correct_values(self, qtbot, mock_context):
        """Test that dialog shows all values from the database."""
        from pysaurus.interface.pyside6.dialogs.property_values_dialog import (
            PropertyValuesDialog,
        )

        prop_types = mock_context.get_prop_types()
        genre_prop = next(pt for pt in prop_types if pt["name"] == "genre")

        dialog = PropertyValuesDialog("genre", genre_prop, mock_context)
        qtbot.addWidget(dialog)

        displayed_values = set()
        for i in range(dialog.values_list.count()):
            item = dialog.values_list.item(i)
            displayed_values.add(item.data(Qt.ItemDataRole.UserRole))

        assert displayed_values == {"action", "comedy", "drama", "romance"}

    def test_dialog_shows_modifier_buttons(self, qtbot, mock_context):
        """Test that dialog shows buttons for all available modifiers."""
        from pysaurus.properties.property_value_modifier import PropertyValueModifier
        from pysaurus.interface.pyside6.dialogs.property_values_dialog import (
            PropertyValuesDialog,
        )

        prop_types = mock_context.get_prop_types()
        genre_prop = next(pt for pt in prop_types if pt["name"] == "genre")

        dialog = PropertyValuesDialog("genre", genre_prop, mock_context)
        qtbot.addWidget(dialog)

        expected_modifiers = PropertyValueModifier.get_modifiers()
        assert (
            len(expected_modifiers) >= 5
        )  # capitalize, lowercase, uppercase, titlecase, strip

        # Check each modifier has a corresponding button
        buttons = dialog.findChildren(type(dialog.btn_delete))
        button_texts = [btn.text().lower().replace(" ", "_") for btn in buttons]
        for mod_name in expected_modifiers:
            assert mod_name.replace("_", " ").title().lower().replace(
                " ", "_"
            ) in button_texts or any(mod_name in text for text in button_texts), (
                f"No button found for modifier '{mod_name}'"
            )


class TestPropertyValuesDialogModifiers:
    """Tests for applying modifiers to property values."""

    def _get_all_genre_values(self, mock_context):
        """Helper: get all genre values as a flat set."""
        values = mock_context.get_property_values("genre")
        return {v for vals in values.values() for v in vals}

    def _apply_modifier(self, qtbot, mock_context, modifier_name, monkeypatch):
        """Helper: create dialog and apply a modifier."""
        from pysaurus.interface.pyside6.dialogs.property_values_dialog import (
            PropertyValuesDialog,
        )

        prop_types = mock_context.get_prop_types()
        genre_prop = next(pt for pt in prop_types if pt["name"] == "genre")

        dialog = PropertyValuesDialog("genre", genre_prop, mock_context)
        qtbot.addWidget(dialog)

        # Auto-accept the confirmation dialog
        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )

        # Click the modifier button
        dialog._on_apply_modifier(modifier_name)

        return dialog

    def test_apply_uppercase(self, qtbot, mock_context, monkeypatch):
        """Test that uppercase modifier converts all values to uppercase."""
        before = self._get_all_genre_values(mock_context)
        assert "action" in before  # lowercase initially

        dialog = self._apply_modifier(qtbot, mock_context, "uppercase", monkeypatch)

        after = self._get_all_genre_values(mock_context)
        assert after == {"ACTION", "COMEDY", "DRAMA", "ROMANCE"}
        assert dialog.was_modified()

    def test_apply_lowercase(self, qtbot, mock_context, monkeypatch):
        """Test that lowercase modifier keeps lowercase values (no-op here)."""
        # Values are already lowercase, so no change expected
        before = self._get_all_genre_values(mock_context)
        assert all(v == v.lower() for v in before)

        self._apply_modifier(qtbot, mock_context, "lowercase", monkeypatch)

        after = self._get_all_genre_values(mock_context)
        assert after == before

    def test_apply_capitalize(self, qtbot, mock_context, monkeypatch):
        """Test that capitalize modifier capitalizes first letter only."""
        self._apply_modifier(qtbot, mock_context, "capitalize", monkeypatch)

        after = self._get_all_genre_values(mock_context)
        assert after == {"Action", "Comedy", "Drama", "Romance"}

    def test_apply_titlecase(self, qtbot, mock_context, monkeypatch):
        """Test that titlecase modifier title-cases values."""
        self._apply_modifier(qtbot, mock_context, "titlecase", monkeypatch)

        after = self._get_all_genre_values(mock_context)
        assert after == {"Action", "Comedy", "Drama", "Romance"}

    def test_apply_strip(self, qtbot, mock_context, monkeypatch):
        """Test that strip modifier removes whitespace (no-op for clean values)."""
        before = self._get_all_genre_values(mock_context)

        self._apply_modifier(qtbot, mock_context, "strip", monkeypatch)

        after = self._get_all_genre_values(mock_context)
        assert after == before  # Already clean, no change

    def test_modifier_updates_dialog_display(self, qtbot, mock_context, monkeypatch):
        """Test that applying a modifier refreshes the dialog's value list."""
        dialog = self._apply_modifier(qtbot, mock_context, "uppercase", monkeypatch)

        # After applying uppercase, the dialog should have reloaded values
        displayed_values = set()
        for i in range(dialog.values_list.count()):
            item = dialog.values_list.item(i)
            displayed_values.add(item.data(Qt.ItemDataRole.UserRole))

        assert displayed_values == {"ACTION", "COMEDY", "DRAMA", "ROMANCE"}

    def test_modifier_preserves_per_video_assignment(
        self, qtbot, mock_context, monkeypatch
    ):
        """Test that modifiers preserve which videos have which values."""
        # Before: video 1 has ["action", "comedy"], video 2 has ["drama"]
        before = mock_context.get_property_values("genre")
        video_with_two = [vid for vid, vals in before.items() if len(vals) == 2]
        assert len(video_with_two) >= 1

        self._apply_modifier(qtbot, mock_context, "uppercase", monkeypatch)

        after = mock_context.get_property_values("genre")
        # Same video should still have 2 values
        for vid in video_with_two:
            assert len(after[vid]) == 2

    def test_modifier_decline_does_nothing(self, qtbot, mock_context, monkeypatch):
        """Test that declining the confirmation dialog does not modify values."""
        from pysaurus.interface.pyside6.dialogs.property_values_dialog import (
            PropertyValuesDialog,
        )

        before = self._get_all_genre_values(mock_context)

        prop_types = mock_context.get_prop_types()
        genre_prop = next(pt for pt in prop_types if pt["name"] == "genre")

        dialog = PropertyValuesDialog("genre", genre_prop, mock_context)
        qtbot.addWidget(dialog)

        # Decline the confirmation
        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.No,
        )

        dialog._on_apply_modifier("uppercase")

        after = self._get_all_genre_values(mock_context)
        assert after == before
        assert not dialog.was_modified()


class TestPropertyValuesDialogDelete:
    """Tests for deleting property values."""

    def test_delete_single_value(self, qtbot, mock_context, monkeypatch):
        """Test deleting a single value from all videos."""
        from pysaurus.interface.pyside6.dialogs.property_values_dialog import (
            PropertyValuesDialog,
        )

        prop_types = mock_context.get_prop_types()
        genre_prop = next(pt for pt in prop_types if pt["name"] == "genre")

        dialog = PropertyValuesDialog("genre", genre_prop, mock_context)
        qtbot.addWidget(dialog)

        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )

        # Delete "drama" value
        dialog._delete_values(["drama"])

        # Verify database
        all_values = mock_context.get_property_values("genre")
        flat_values = {v for vals in all_values.values() for v in vals}
        assert "drama" not in flat_values
        assert "action" in flat_values  # Others unchanged

        # Verify dialog display updated
        displayed_values = set()
        for i in range(dialog.values_list.count()):
            item = dialog.values_list.item(i)
            displayed_values.add(item.data(Qt.ItemDataRole.UserRole))
        assert "drama" not in displayed_values

    def test_delete_multiple_values(self, qtbot, mock_context, monkeypatch):
        """Test deleting multiple values at once."""
        from pysaurus.interface.pyside6.dialogs.property_values_dialog import (
            PropertyValuesDialog,
        )

        prop_types = mock_context.get_prop_types()
        genre_prop = next(pt for pt in prop_types if pt["name"] == "genre")

        dialog = PropertyValuesDialog("genre", genre_prop, mock_context)
        qtbot.addWidget(dialog)

        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )

        dialog._delete_values(["drama", "romance"])

        all_values = mock_context.get_property_values("genre")
        flat_values = {v for vals in all_values.values() for v in vals}
        assert "drama" not in flat_values
        assert "romance" not in flat_values
        assert "action" in flat_values
        assert "comedy" in flat_values


class TestPropertyValuesDialogRename:
    """Tests for renaming property values."""

    def test_rename_value(self, qtbot, mock_context, monkeypatch):
        """Test renaming a value updates the database and dialog."""
        from pysaurus.interface.pyside6.dialogs.property_values_dialog import (
            PropertyValuesDialog,
        )
        from PySide6.QtWidgets import QInputDialog

        prop_types = mock_context.get_prop_types()
        genre_prop = next(pt for pt in prop_types if pt["name"] == "genre")

        dialog = PropertyValuesDialog("genre", genre_prop, mock_context)
        qtbot.addWidget(dialog)

        # Mock QInputDialog to return new name
        monkeypatch.setattr(
            QInputDialog, "getText", lambda *args, **kwargs: ("sci-fi", True)
        )

        dialog._rename_value("drama")

        # Verify database
        all_values = mock_context.get_property_values("genre")
        flat_values = {v for vals in all_values.values() for v in vals}
        assert "drama" not in flat_values
        assert "sci-fi" in flat_values

        # Verify dialog display
        displayed_values = set()
        for i in range(dialog.values_list.count()):
            item = dialog.values_list.item(i)
            displayed_values.add(item.data(Qt.ItemDataRole.UserRole))
        assert "drama" not in displayed_values
        assert "sci-fi" in displayed_values

    def test_rename_to_existing_merges(self, qtbot, mock_context, monkeypatch):
        """Test renaming to an existing value merges them."""
        from pysaurus.interface.pyside6.dialogs.property_values_dialog import (
            PropertyValuesDialog,
        )
        from PySide6.QtWidgets import QInputDialog

        prop_types = mock_context.get_prop_types()
        genre_prop = next(pt for pt in prop_types if pt["name"] == "genre")

        dialog = PropertyValuesDialog("genre", genre_prop, mock_context)
        qtbot.addWidget(dialog)

        # Mock input to return "action" (already exists)
        monkeypatch.setattr(
            QInputDialog, "getText", lambda *args, **kwargs: ("action", True)
        )
        # Accept the merge confirmation
        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )

        dialog._rename_value("drama")

        # Verify "drama" is gone
        all_values = mock_context.get_property_values("genre")
        flat_values = {v for vals in all_values.values() for v in vals}
        assert "drama" not in flat_values
        assert "action" in flat_values

        # Number of distinct values should have decreased
        assert len(flat_values) == 3  # action, comedy, romance


class TestPropertyValuesDialogFromPropertiesPage:
    """Tests for the full flow: PropertiesPage → PropertyValuesDialog."""

    def test_manage_values_opens_dialog(self, qtbot, mock_context, monkeypatch):
        """Test that Manage Values action opens PropertyValuesDialog."""
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Track dialog creation
        dialogs_created = []

        from pysaurus.interface.pyside6.dialogs import property_values_dialog

        original_init = property_values_dialog.PropertyValuesDialog.__init__

        def tracking_init(self_dialog, *args, **kwargs):
            original_init(self_dialog, *args, **kwargs)
            dialogs_created.append(self_dialog)

        # Mock exec to not block, and track init
        monkeypatch.setattr(
            property_values_dialog.PropertyValuesDialog, "__init__", tracking_init
        )
        monkeypatch.setattr(
            property_values_dialog.PropertyValuesDialog,
            "exec",
            lambda self_dialog: None,
        )

        # Trigger "Manage Values" for genre
        page._on_manage_values("genre")

        assert len(dialogs_created) == 1
        assert dialogs_created[0].prop_name == "genre"

    def test_full_flow_modifier_from_page(self, qtbot, mock_context, monkeypatch):
        """Test the full flow: page → dialog → modifier → DB changed."""
        from pysaurus.interface.pyside6.dialogs.property_values_dialog import (
            PropertyValuesDialog,
        )
        from pysaurus.interface.pyside6.pages.properties_page import PropertiesPage

        page = PropertiesPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Get the genre property type
        prop_type = next(
            pt for pt in mock_context.get_prop_types() if pt["name"] == "genre"
        )

        # Create and interact with dialog (simulating what _on_manage_values does)
        dialog = PropertyValuesDialog("genre", prop_type, mock_context, page)
        qtbot.addWidget(dialog)

        # Verify initial values
        assert dialog.values_list.count() == 4

        # Auto-accept confirmation
        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )

        # Apply capitalize modifier
        dialog._on_apply_modifier("capitalize")

        # Verify database was changed
        all_values = mock_context.get_property_values("genre")
        flat_values = {v for vals in all_values.values() for v in vals}
        assert flat_values == {"Action", "Comedy", "Drama", "Romance"}

        # Verify dialog display was updated
        displayed_values = set()
        for i in range(dialog.values_list.count()):
            item = dialog.values_list.item(i)
            displayed_values.add(item.data(Qt.ItemDataRole.UserRole))
        assert displayed_values == {"Action", "Comedy", "Drama", "Romance"}

        # Verify dialog reports modification
        assert dialog.was_modified()
