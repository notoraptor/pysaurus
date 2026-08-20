"""
Tests for PySide6 dialogs.

Tests BatchEditPropertyDialog and VideoPropertiesDialog.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTabWidget

from pysaurus.core.language import say
from pysaurus.interface.kyuti.dialogs.batch_edit_property_dialog import (
    BatchEditPropertyDialog,
)
from pysaurus.interface.kyuti.dialogs.video_properties_dialog import (
    VideoPropertiesDialog,
)
from pysaurus.interface.kyuti.widgets.multiple_values_widget import (
    MODIFIED_COLOR,
    MultipleValuesWidget,
)
from pysaurus.properties.properties import PropType
from tests.mocks.mock_database import MockVideoPattern


class TestBatchEditPropertyDialog:
    """Tests for BatchEditPropertyDialog."""

    @pytest.fixture
    def prop_type_string_multiple(self):
        """String multiple property type."""
        return PropType(
            name="genre", type="str", multiple=True, default=[], enumeration=None
        )

    @pytest.fixture
    def values_and_counts(self):
        """Sample values with counts."""
        return [["action", 3], ["comedy", 2], ["drama", 1]]

    def test_dialog_creation(self, qtbot, prop_type_string_multiple, values_and_counts):
        """Test that dialog can be created."""
        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        assert dialog.prop_name == "genre"
        assert dialog.nb_videos == 5

    def test_bool_combo_is_built_from_the_implicit_domain(self, qtbot):
        """A bool carries no enumeration, yet still offers a constrained choice.

        The combo used to hardcode its own "true"/"false" items; it now reads
        PropType.possible_values, like any enumerated property.
        """
        prop_type = PropType.define("watched", "bool", False, False)
        dialog = BatchEditPropertyDialog("watched", prop_type, 5, [[True, 2]])
        qtbot.addWidget(dialog)

        combo = dialog.value_input
        labels = [combo.itemText(i) for i in range(combo.count())]
        data = [combo.itemData(i) for i in range(combo.count())]
        # Picked, so the Yes/No register -- in domain order, False first.
        assert labels == ["No", "Yes"]
        assert data == [False, True]

    def test_bool_values_are_listed_in_the_picked_register(self, qtbot):
        """The current-values list shows "Yes (2)", not "True (2)"."""
        prop_type = PropType.define("watched", "bool", False, False)
        dialog = BatchEditPropertyDialog("watched", prop_type, 5, [[True, 2]])
        qtbot.addWidget(dialog)

        assert dialog.current_list.count() == 1
        labels = dialog.current_list.findChildren(QLabel)
        assert any(label.text() == "Yes (2)" for label in labels)

    def test_dialog_shows_current_values(
        self, qtbot, prop_type_string_multiple, values_and_counts
    ):
        """Test that dialog shows current values with counts."""
        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        # Current list should have all values
        assert dialog.current_list.count() == 3

    def test_remove_one(self, qtbot, prop_type_string_multiple, values_and_counts):
        """Test moving a value to remove list via inline button."""
        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        dialog._remove_one("action")

        assert dialog.current_list.count() == 2
        assert dialog.remove_list.count() == 1

    def test_add_one(self, qtbot, prop_type_string_multiple, values_and_counts):
        """Test moving a value to add list via inline button."""
        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        dialog._add_one("action")

        assert dialog.current_list.count() == 2
        assert dialog.add_list.count() == 1

    def test_restore_one(self, qtbot, prop_type_string_multiple, values_and_counts):
        """Test restoring a value from remove list via inline button."""
        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        dialog._remove_one("action")
        assert dialog.remove_list.count() == 1

        dialog._restore_one("action")

        assert dialog.current_list.count() == 3
        assert dialog.remove_list.count() == 0

    def test_add_new_value(self, qtbot, prop_type_string_multiple, values_and_counts):
        """Test adding a new value."""
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
        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        # Move action to remove
        dialog._remove_one("action")

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
        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)

        dialog._move_all_to_remove()

        assert dialog.current_list.count() == 0
        assert dialog.remove_list.count() == 3


class TestBatchEditPropertyDialogButtons:
    """Tests that inline buttons are clickable."""

    @pytest.fixture
    def prop_type_string_multiple(self):
        return PropType(
            name="genre", type="str", multiple=True, default=[], enumeration=None
        )

    @pytest.fixture
    def values_and_counts(self):
        return [["action", 3], ["comedy", 2], ["drama", 1]]

    def _find_button(self, entry_list, entry_index, button_text):
        """Find a QPushButton in an entry widget by index and button text."""
        # Get the entry widget at the given index
        item = entry_list._layout.itemAt(entry_index)
        assert item is not None, f"No item at index {entry_index}"
        widget = item.widget()
        assert widget is not None, f"No widget at index {entry_index}"
        # Find button by text
        for btn in widget.findChildren(QPushButton):
            if btn.text() == button_text:
                return btn
        raise AssertionError(
            f"No button with text '{button_text}' in entry {entry_index}"
        )

    def test_click_remove_button(
        self, qtbot, prop_type_string_multiple, values_and_counts
    ):
        """Test that clicking the remove button on a current entry works."""
        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitExposed(dialog)

        assert dialog.current_list.count() == 3

        # Click the "←" (remove) button on the first current entry
        btn = self._find_button(dialog.current_list, 0, "←")
        qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)

        assert dialog.current_list.count() == 2
        assert dialog.remove_list.count() == 1

    def test_click_restore_button(
        self, qtbot, prop_type_string_multiple, values_and_counts
    ):
        """Test that clicking the restore button on a removed entry works."""
        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitExposed(dialog)

        # First remove one
        dialog._remove_one("action")
        assert dialog.remove_list.count() == 1

        # Click the "→" (restore) button on the first remove entry
        btn = self._find_button(dialog.remove_list, 0, "→")
        qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)

        assert dialog.remove_list.count() == 0
        assert dialog.current_list.count() == 3

    def test_click_add_button(
        self, qtbot, prop_type_string_multiple, values_and_counts
    ):
        """Test that clicking the add button on a current entry works."""
        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitExposed(dialog)

        # Click the "→" (add) button on the first current entry
        btn = self._find_button(dialog.current_list, 0, "→")
        qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)

        assert dialog.current_list.count() == 2
        assert dialog.add_list.count() == 1

    def test_click_cancel_button(
        self, qtbot, prop_type_string_multiple, values_and_counts
    ):
        """Test that clicking the cancel button on an added entry works."""
        dialog = BatchEditPropertyDialog(
            "genre", prop_type_string_multiple, 5, values_and_counts
        )
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitExposed(dialog)

        # First add one
        dialog._add_one("action")
        assert dialog.add_list.count() == 1

        # Click the "←" (cancel) button on the first add entry
        btn = self._find_button(dialog.add_list, 0, "←")
        qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)

        assert dialog.add_list.count() == 0
        assert dialog.current_list.count() == 3


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

    def test_dialog_creation(self, qtbot, sample_video, mock_context):
        """Test that dialog can be created."""
        prop_types = mock_context.get_prop_types()
        dialog = VideoPropertiesDialog(sample_video, prop_types, mock_context)
        qtbot.addWidget(dialog)

        assert dialog.video == sample_video
        assert "Test Video" in dialog.windowTitle()

    def test_dialog_has_tabs(self, qtbot, sample_video, mock_context):
        """Test that dialog has Info and Properties tabs."""
        prop_types = mock_context.get_prop_types()
        dialog = VideoPropertiesDialog(sample_video, prop_types, mock_context)
        qtbot.addWidget(dialog)

        # Find tab widget
        tabs = dialog.findChild(QTabWidget)
        assert tabs is not None
        assert tabs.count() == 2

    def test_dialog_loads_properties(self, qtbot, sample_video, mock_context):
        """Test that dialog loads video properties."""
        prop_types = mock_context.get_prop_types()
        dialog = VideoPropertiesDialog(sample_video, prop_types, mock_context)
        qtbot.addWidget(dialog)

        # Should have property widgets
        assert len(dialog._property_widgets) == 2  # genre, rating

    def test_dialog_shows_video_info(self, qtbot, sample_video, mock_context):
        """Test that dialog shows video info."""
        prop_types = mock_context.get_prop_types()
        dialog = VideoPropertiesDialog(sample_video, prop_types, mock_context)
        qtbot.addWidget(dialog)

        # Dialog should have valid size and be properly constructed
        assert dialog.minimumWidth() > 0
        assert dialog.minimumHeight() > 0

    def test_removing_a_value_leaves_focus_in_its_own_property(
        self, qtbot, mock_context
    ):
        """The cross must not take focus, or removal scrolls the form away.

        Every property sits in one shared scroll area. A focused button hands
        focus to the next widget in the chain when it is destroyed -- the first
        cross of the *next* property -- and the scroll area then jumps there.
        """
        prop_types = [
            PropType(name=name, type="str", multiple=True, default=[], enumeration=None)
            for name in ("alpha", "beta")
        ]
        video = MockVideoPattern(
            {
                "video_id": 1,
                "filename": "/videos/test.mp4",
                "file_size": 1,
                "mtime": 1.0,
                "duration": 1,
                "duration_time_base": 1,
                "height": 1080,
                "width": 1920,
                "meta_title": "Test Video",
                "found": True,
                "unreadable": False,
                "watched": False,
                "with_thumbnails": False,
                "properties": {"alpha": ["a1", "a2"], "beta": ["b1", "b2"]},
            }
        )
        dialog = VideoPropertiesDialog(video, prop_types, mock_context)
        qtbot.addWidget(dialog)
        dialog.show()
        # Focus is only handed over inside the active window.
        dialog.activateWindow()
        QApplication.processEvents()

        alpha = dialog._property_widgets["alpha"]
        beta = dialog._property_widgets["beta"]
        alpha.input_edit.setFocus()
        assert dialog.isActiveWindow()

        last = alpha.list_widget.item(alpha.list_widget.count() - 1)
        QTest.mouseClick(
            alpha.list_widget.itemWidget(last).remove_button, Qt.MouseButton.LeftButton
        )

        assert alpha.get_values() == ["a1"]
        assert alpha.isAncestorOf(dialog.focusWidget())
        assert not beta.isAncestorOf(dialog.focusWidget())


class TestMultipleValuesWidget:
    """Tests for MultipleValuesWidget used in VideoPropertiesDialog."""

    @pytest.fixture
    def prop_type_multiple(self):
        """Multiple string property type."""
        return PropType(
            name="tags", type="str", multiple=True, default=[], enumeration=None
        )

    @pytest.fixture
    def prop_type_enum(self):
        """Enumeration property type."""
        return PropType(
            name="status",
            type="str",
            multiple=True,
            default=[],
            enumeration=["new", "watched", "archived"],
        )

    def test_widget_creation_free_form(self, qtbot, prop_type_multiple):
        """Test creating widget for free-form values."""
        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        assert hasattr(widget, "list_widget")
        assert hasattr(widget, "input_edit")

    def test_widget_creation_enum(self, qtbot, prop_type_enum):
        """Test creating widget for enumeration values."""
        widget = MultipleValuesWidget(prop_type_enum)
        qtbot.addWidget(widget)

        assert hasattr(widget, "checkboxes")
        assert len(widget.checkboxes) == 3

    def test_set_values_free_form(self, qtbot, prop_type_multiple):
        """Test setting values in free-form widget."""
        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        widget.set_values(["tag1", "tag2", "tag3"])

        assert widget.list_widget.count() == 3

    def test_get_values_free_form(self, qtbot, prop_type_multiple):
        """Test getting values from free-form widget."""
        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        widget.set_values(["tag1", "tag2"])

        values = widget.get_values()
        assert "tag1" in values
        assert "tag2" in values

    def test_set_values_enum(self, qtbot, prop_type_enum):
        """Test setting values in enum widget."""
        widget = MultipleValuesWidget(prop_type_enum)
        qtbot.addWidget(widget)

        widget.set_values(["new", "watched"])

        assert widget.checkboxes["new"].isChecked()
        assert widget.checkboxes["watched"].isChecked()
        assert not widget.checkboxes["archived"].isChecked()

    def test_get_values_enum(self, qtbot, prop_type_enum):
        """Test getting values from enum widget."""
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
        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        widget.input_edit.setText("new_tag")
        widget._add_value()

        assert widget.list_widget.count() == 1
        assert widget.input_edit.text() == ""

    def test_clear_values(self, qtbot, prop_type_multiple):
        """Test clearing values."""
        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        widget.set_values(["tag1", "tag2"])
        widget._clear_values()

        assert widget.list_widget.count() == 0

    def test_reset_values(self, qtbot, prop_type_multiple):
        """Test resetting to initial values."""
        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        widget.set_values(["tag1", "tag2"])
        widget._clear_values()
        widget._reset_values()

        assert widget.list_widget.count() == 2

    @staticmethod
    def _rows(widget) -> list:
        """The per-value row widgets, top to bottom."""
        return [
            widget.list_widget.itemWidget(widget.list_widget.item(i))
            for i in range(widget.list_widget.count())
        ]

    def test_remove_value_from_its_own_row(self, qtbot, prop_type_multiple):
        """A value is removed by the cross on its own row."""
        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        widget.set_values(["tag1", "tag2", "tag3"])
        self._rows(widget)[1].remove_button.click()

        assert widget.get_values() == ["tag1", "tag3"]

    def test_removed_value_comes_back_on_reset(self, qtbot, prop_type_multiple):
        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        widget.set_values(["tag1", "tag2"])
        self._rows(widget)[0].remove_button.click()
        widget._reset_values()

        assert widget.get_values() == ["tag1", "tag2"]

    def test_added_value_is_marked_modified(self, qtbot, prop_type_multiple):
        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        widget.set_values(["tag1"])
        widget.input_edit.setText("tag2")
        widget._add_value()

        rows = self._rows(widget)
        assert rows[0].label.styleSheet() == ""
        assert MODIFIED_COLOR in rows[1].label.styleSheet()

    def test_untracked_widget_marks_nothing(self, qtbot, prop_type_multiple):
        """Batch editing has no initial state, hence no Reset and no coloring."""
        widget = MultipleValuesWidget(prop_type_multiple, track_changes=False)
        qtbot.addWidget(widget)

        widget.input_edit.setText("tag1")
        widget._add_value()

        assert self._rows(widget)[0].label.styleSheet() == ""
        assert not [
            btn
            for btn in widget.findChildren(QPushButton)
            if btn.text() == say("Reset")
        ]

    def test_long_value_keeps_full_text_in_tooltip(self, qtbot, prop_type_multiple):
        """The label elides, so the whole value must stay reachable."""
        long_value = "a very long tag value " * 10
        widget = MultipleValuesWidget(prop_type_multiple)
        qtbot.addWidget(widget)

        widget.set_values([long_value])

        row = self._rows(widget)[0]
        assert row.label.toolTip() == long_value
        assert widget.get_values() == [long_value]
