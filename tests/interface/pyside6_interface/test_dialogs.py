"""
Tests for PySide6 dialogs.

Tests BatchEditPropertyDialog and VideoPropertiesDialog.
"""

import pytest

from tests.mocks.mock_database import MockVideoPattern


class TestBatchEditPropertyDialog:
    """Tests for BatchEditPropertyDialog."""

    @pytest.fixture
    def prop_type_string_multiple(self):
        """String multiple property type."""
        return {
            "name": "genre",
            "type": "str",
            "multiple": True,
            "enumeration": None,
            "defaultValues": [],
        }

    @pytest.fixture
    def values_and_counts(self):
        """Sample values with counts."""
        return [["action", 3], ["comedy", 2], ["drama", 1]]

    def test_dialog_creation(self, qtbot, prop_type_string_multiple, values_and_counts):
        """Test that dialog can be created."""
        from pysaurus.interface.pyside6.dialogs.batch_edit_property_dialog import (
            BatchEditPropertyDialog,
        )

        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        assert dialog.prop_name == "genre"
        assert dialog.nb_videos == 5

    def test_dialog_shows_current_values(
        self, qtbot, prop_type_string_multiple, values_and_counts
    ):
        """Test that dialog shows current values with counts."""
        from pysaurus.interface.pyside6.dialogs.batch_edit_property_dialog import (
            BatchEditPropertyDialog,
        )

        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        # Current list should have all values
        assert dialog.current_list.count() == 3

    def test_move_to_remove(self, qtbot, prop_type_string_multiple, values_and_counts):
        """Test moving values to remove list."""
        from pysaurus.interface.pyside6.dialogs.batch_edit_property_dialog import (
            BatchEditPropertyDialog,
        )

        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        # Select first item in current list
        dialog.current_list.setCurrentRow(0)

        # Move to remove
        dialog._move_to_remove()

        # Check lists
        assert dialog.current_list.count() == 2
        assert dialog.remove_list.count() == 1

    def test_move_to_add(self, qtbot, prop_type_string_multiple, values_and_counts):
        """Test moving values to add list."""
        from pysaurus.interface.pyside6.dialogs.batch_edit_property_dialog import (
            BatchEditPropertyDialog,
        )

        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        # Select first item in current list
        dialog.current_list.setCurrentRow(0)

        # Move to add
        dialog._move_to_add()

        # Check lists
        assert dialog.current_list.count() == 2
        assert dialog.add_list.count() == 1

    def test_restore_from_remove(
        self, qtbot, prop_type_string_multiple, values_and_counts
    ):
        """Test restoring values from remove list."""
        from pysaurus.interface.pyside6.dialogs.batch_edit_property_dialog import (
            BatchEditPropertyDialog,
        )

        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        # Move to remove first
        dialog.current_list.setCurrentRow(0)
        dialog._move_to_remove()
        assert dialog.remove_list.count() == 1

        # Restore
        dialog.remove_list.setCurrentRow(0)
        dialog._restore_from_remove()

        assert dialog.current_list.count() == 3
        assert dialog.remove_list.count() == 0

    def test_add_new_value(self, qtbot, prop_type_string_multiple, values_and_counts):
        """Test adding a new value."""
        from pysaurus.interface.pyside6.dialogs.batch_edit_property_dialog import (
            BatchEditPropertyDialog,
        )

        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        # Add new value
        dialog.value_input.setText("horror")
        dialog._add_new_value()

        # Should be in add list
        assert dialog.add_list.count() == 1

    def test_get_changes(self, qtbot, prop_type_string_multiple, values_and_counts):
        """Test getting changes."""
        from pysaurus.interface.pyside6.dialogs.batch_edit_property_dialog import (
            BatchEditPropertyDialog,
        )

        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        # Move action to remove
        dialog.current_list.setCurrentRow(0)
        dialog._move_to_remove()

        # Add new value
        dialog.value_input.setText("horror")
        dialog._add_new_value()

        # Get changes
        to_add, to_remove = dialog.get_changes()

        assert "horror" in to_add
        assert "action" in to_remove

    def test_move_all_to_remove(
        self, qtbot, prop_type_string_multiple, values_and_counts
    ):
        """Test moving all values to remove."""
        from pysaurus.interface.pyside6.dialogs.batch_edit_property_dialog import (
            BatchEditPropertyDialog,
        )

        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        dialog._move_all_to_remove()

        assert dialog.current_list.count() == 0
        assert dialog.remove_list.count() == 3


class TestVideoPropertiesDialog:
    """Tests for VideoPropertiesDialog."""

    @pytest.fixture
    def sample_video(self):
        """Sample video for testing."""
        return MockVideoPattern(
            {
                "video_id": 1,
                "filename": "/videos/test.mp4",
                "file_size": 104857600,
                "mtime": 1700000000.0,
                "duration": 3600,
                "duration_time_base": 1,
                "height": 1080,
                "width": 1920,
                "meta_title": "Test Video",
                "found": True,
                "unreadable": False,
                "watched": False,
                "with_thumbnails": True,
                "video_codec": "h264",
                "video_codec_description": "H.264",
                "audio_codec": "aac",
                "channels": 2,
                "sample_rate": 44100,
                "audio_bit_rate": 128000,
                "container_format": "mp4",
                "frame_rate_num": 30,
                "frame_rate_den": 1,
                "date_entry_modified": "2024-01-15",
                "similarity_id": None,
                "properties": {"genre": ["action", "comedy"], "rating": [8]},
            }
        )

    def test_dialog_creation(self, qtbot, sample_video, mock_database):
        """Test that dialog can be created."""
        from pysaurus.interface.pyside6.dialogs.video_properties_dialog import (
            VideoPropertiesDialog,
        )

        prop_types = mock_database.get_prop_types()
        dialog = VideoPropertiesDialog(sample_video, prop_types, mock_database)
        qtbot.addWidget(dialog)

        assert dialog.video == sample_video
        assert "Test Video" in dialog.windowTitle()

    def test_dialog_has_tabs(self, qtbot, sample_video, mock_database):
        """Test that dialog has Info and Properties tabs."""
        from pysaurus.interface.pyside6.dialogs.video_properties_dialog import (
            VideoPropertiesDialog,
        )

        prop_types = mock_database.get_prop_types()
        dialog = VideoPropertiesDialog(sample_video, prop_types, mock_database)
        qtbot.addWidget(dialog)

        # Find tab widget
        from PySide6.QtWidgets import QTabWidget

        tabs = dialog.findChild(QTabWidget)
        assert tabs is not None
        assert tabs.count() == 2

    def test_dialog_loads_properties(self, qtbot, sample_video, mock_database):
        """Test that dialog loads video properties."""
        from pysaurus.interface.pyside6.dialogs.video_properties_dialog import (
            VideoPropertiesDialog,
        )

        prop_types = mock_database.get_prop_types()
        dialog = VideoPropertiesDialog(sample_video, prop_types, mock_database)
        qtbot.addWidget(dialog)

        # Should have property widgets
        assert len(dialog._property_widgets) == 2  # genre, rating

    def test_dialog_shows_video_info(self, qtbot, sample_video, mock_database):
        """Test that dialog shows video info."""
        from pysaurus.interface.pyside6.dialogs.video_properties_dialog import (
            VideoPropertiesDialog,
        )

        prop_types = mock_database.get_prop_types()
        dialog = VideoPropertiesDialog(sample_video, prop_types, mock_database)
        qtbot.addWidget(dialog)

        # Dialog should have valid size and be properly constructed
        assert dialog.minimumWidth() > 0
        assert dialog.minimumHeight() > 0


class TestMultipleValuesWidget:
    """Tests for MultipleValuesWidget used in VideoPropertiesDialog."""

    @pytest.fixture
    def prop_type_multiple(self):
        """Multiple string property type."""
        return {"name": "tags", "type": "str", "multiple": True, "enumeration": None}

    @pytest.fixture
    def prop_type_enum(self):
        """Enumeration property type."""
        return {
            "name": "status",
            "type": "str",
            "multiple": True,
            "enumeration": ["new", "watched", "archived"],
        }

    def test_widget_creation_free_form(self, qtbot, prop_type_multiple):
        """Test creating widget for free-form values."""
        from pysaurus.interface.pyside6.dialogs.video_properties_dialog import (
            MultipleValuesWidget,
        )

        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        assert hasattr(widget, "list_widget")
        assert hasattr(widget, "input_edit")

    def test_widget_creation_enum(self, qtbot, prop_type_enum):
        """Test creating widget for enumeration values."""
        from pysaurus.interface.pyside6.dialogs.video_properties_dialog import (
            MultipleValuesWidget,
        )

        widget = MultipleValuesWidget(prop_type_enum)
        qtbot.addWidget(widget)

        assert hasattr(widget, "checkboxes")
        assert len(widget.checkboxes) == 3

    def test_set_values_free_form(self, qtbot, prop_type_multiple):
        """Test setting values in free-form widget."""
        from pysaurus.interface.pyside6.dialogs.video_properties_dialog import (
            MultipleValuesWidget,
        )

        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        widget.set_values(["tag1", "tag2", "tag3"])

        assert widget.list_widget.count() == 3

    def test_get_values_free_form(self, qtbot, prop_type_multiple):
        """Test getting values from free-form widget."""
        from pysaurus.interface.pyside6.dialogs.video_properties_dialog import (
            MultipleValuesWidget,
        )

        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        widget.set_values(["tag1", "tag2"])

        values = widget.get_values()
        assert "tag1" in values
        assert "tag2" in values

    def test_set_values_enum(self, qtbot, prop_type_enum):
        """Test setting values in enum widget."""
        from pysaurus.interface.pyside6.dialogs.video_properties_dialog import (
            MultipleValuesWidget,
        )

        widget = MultipleValuesWidget(prop_type_enum)
        qtbot.addWidget(widget)

        widget.set_values(["new", "watched"])

        assert widget.checkboxes["new"].isChecked()
        assert widget.checkboxes["watched"].isChecked()
        assert not widget.checkboxes["archived"].isChecked()

    def test_get_values_enum(self, qtbot, prop_type_enum):
        """Test getting values from enum widget."""
        from pysaurus.interface.pyside6.dialogs.video_properties_dialog import (
            MultipleValuesWidget,
        )

        widget = MultipleValuesWidget(prop_type_enum)
        qtbot.addWidget(widget)

        widget.checkboxes["new"].setChecked(True)
        widget.checkboxes["archived"].setChecked(True)

        values = widget.get_values()
        assert "new" in values
        assert "archived" in values
        assert "watched" not in values

    def test_add_value_free_form(self, qtbot, prop_type_multiple):
        """Test adding value in free-form widget."""
        from pysaurus.interface.pyside6.dialogs.video_properties_dialog import (
            MultipleValuesWidget,
        )

        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        widget.input_edit.setText("new_tag")
        widget._add_value()

        assert widget.list_widget.count() == 1
        assert widget.input_edit.text() == ""

    def test_clear_values(self, qtbot, prop_type_multiple):
        """Test clearing values."""
        from pysaurus.interface.pyside6.dialogs.video_properties_dialog import (
            MultipleValuesWidget,
        )

        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        widget.set_values(["tag1", "tag2"])
        widget._clear_values()

        assert widget.list_widget.count() == 0

    def test_reset_values(self, qtbot, prop_type_multiple):
        """Test resetting to initial values."""
        from pysaurus.interface.pyside6.dialogs.video_properties_dialog import (
            MultipleValuesWidget,
        )

        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        widget.set_values(["tag1", "tag2"])
        widget._clear_values()
        widget._reset_values()

        assert widget.list_widget.count() == 2
