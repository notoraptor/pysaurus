"""
Dialog for viewing and editing video properties.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.duration import Duration
from pysaurus.core.file_size import FileSize
from pysaurus.video.video_pattern import VideoPattern


class NonSubmittingLineEdit(QLineEdit):
    """QLineEdit that doesn't propagate Enter key to parent dialog."""

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Emit returnPressed but don't propagate to parent
            self.returnPressed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


class MultipleValuesWidget(QWidget):
    """Widget for editing multiple values of a property."""

    def __init__(self, prop_type: dict, parent=None):
        super().__init__(parent)
        self.prop_type = prop_type
        self.ptype = prop_type["type"]
        self.enumeration = prop_type.get("enumeration")
        self._initial_values: list = []  # For reset functionality

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        if self.enumeration:
            # Enumeration: show checkboxes for each possible value
            self.checkboxes: dict[str, QCheckBox] = {}
            for value in self.enumeration:
                cb = QCheckBox(str(value))
                cb.setProperty("enum_value", value)
                self.checkboxes[str(value)] = cb
                layout.addWidget(cb)

            # Buttons row for enumeration
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 0, 0, 0)

            btn_reset = QPushButton("Reset")
            btn_reset.setToolTip("Restore initial values")
            btn_reset.clicked.connect(self._reset_values)
            btn_layout.addWidget(btn_reset)

            btn_clear = QPushButton("Clear")
            btn_clear.setToolTip("Uncheck all values")
            btn_clear.clicked.connect(self._clear_values)
            btn_layout.addWidget(btn_clear)

            btn_layout.addStretch()
            layout.addLayout(btn_layout)
        else:
            # Free-form: show list with add/remove buttons
            self.list_widget = QListWidget()
            self.list_widget.setMaximumHeight(100)
            self.list_widget.setSelectionMode(
                QListWidget.SelectionMode.ExtendedSelection
            )
            layout.addWidget(self.list_widget)

            # Input row
            input_layout = QHBoxLayout()
            input_layout.setContentsMargins(0, 0, 0, 0)

            self.input_edit = NonSubmittingLineEdit()
            self.input_edit.setPlaceholderText("Enter value...")
            self.input_edit.returnPressed.connect(self._add_value)
            input_layout.addWidget(self.input_edit)

            btn_add = QPushButton("+")
            btn_add.setFixedWidth(30)
            btn_add.setToolTip("Add value")
            btn_add.clicked.connect(self._add_value)
            input_layout.addWidget(btn_add)

            btn_remove = QPushButton("-")
            btn_remove.setFixedWidth(30)
            btn_remove.setToolTip("Remove selected value(s)")
            btn_remove.clicked.connect(self._remove_selected)
            input_layout.addWidget(btn_remove)

            layout.addLayout(input_layout)

            # Buttons row
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 0, 0, 0)

            btn_reset = QPushButton("Reset")
            btn_reset.setToolTip("Restore initial values")
            btn_reset.clicked.connect(self._reset_values)
            btn_layout.addWidget(btn_reset)

            btn_clear = QPushButton("Clear")
            btn_clear.setToolTip("Remove all values")
            btn_clear.clicked.connect(self._clear_values)
            btn_layout.addWidget(btn_clear)

            btn_layout.addStretch()
            layout.addLayout(btn_layout)

    def _add_value(self):
        """Add a value to the list."""
        text = self.input_edit.text().strip()
        if not text:
            return

        # Validate and convert type
        try:
            if self.ptype == "int":
                value = int(text)
            elif self.ptype == "float":
                value = float(text)
            else:
                value = text

            # Check for duplicates
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).data(Qt.ItemDataRole.UserRole) == value:
                    return  # Already exists

            item = QListWidgetItem(str(value))
            item.setData(Qt.ItemDataRole.UserRole, value)
            self.list_widget.addItem(item)
            self.input_edit.clear()
        except ValueError:
            pass  # Invalid input

    def _remove_selected(self):
        """Remove the selected item(s)."""
        # Get selected items in reverse order to avoid index shifting
        selected = self.list_widget.selectedItems()
        for item in selected:
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)

    def _reset_values(self):
        """Reset to initial values."""
        self._set_values_internal(self._initial_values)

    def _clear_values(self):
        """Clear all values."""
        if self.enumeration:
            for cb in self.checkboxes.values():
                cb.setChecked(False)
        else:
            self.list_widget.clear()

    def _set_values_internal(self, values: list):
        """Internal method to set values without updating initial values."""
        if self.enumeration:
            # Uncheck all first
            for cb in self.checkboxes.values():
                cb.setChecked(False)
            # Check the ones in values
            for value in values:
                key = str(value)
                if key in self.checkboxes:
                    self.checkboxes[key].setChecked(True)
        else:
            self.list_widget.clear()
            for value in values:
                item = QListWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, value)
                self.list_widget.addItem(item)

    def set_values(self, values):
        """Set the current values and store as initial values."""
        # Filter out None values
        if not isinstance(values, (list, tuple)):
            values = [values] if values is not None else []
        else:
            values = [v for v in values if v is not None]

        # Store initial values for reset
        self._initial_values = list(values)

        self._set_values_internal(values)

    def get_values(self) -> list:
        """Get the current values."""
        if self.enumeration:
            result = []
            for cb in self.checkboxes.values():
                if cb.isChecked():
                    value = cb.property("enum_value")
                    result.append(value)
            return result
        else:
            result = []
            for i in range(self.list_widget.count()):
                result.append(self.list_widget.item(i).data(Qt.ItemDataRole.UserRole))
            return result


class VideoPropertiesDialog(QDialog):
    """
    Dialog for viewing video metadata and editing custom properties.

    Tabs:
    - Info: Read-only video metadata
    - Properties: Editable custom properties
    """

    def __init__(self, video: VideoPattern, prop_types: list, database, parent=None):
        super().__init__(parent)
        self.video = video
        self.prop_types = prop_types
        self.database = database
        self._property_widgets: dict[str, QWidget] = {}

        self.setWindowTitle(f"Properties - {video.title}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._setup_ui()
        self._load_properties()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        # Tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Info tab
        info_tab = self._create_info_tab()
        tabs.addTab(info_tab, "Info")

        # Properties tab
        props_tab = self._create_properties_tab()
        tabs.addTab(props_tab, "Properties")

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        # Disable auto-default to prevent ENTER from submitting the form
        for button in button_box.buttons():
            button.setAutoDefault(False)
            button.setDefault(False)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_info_tab(self) -> QWidget:
        """Create the info tab with video metadata."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        widget = QWidget()
        layout = QVBoxLayout(widget)

        # File info
        file_group = QGroupBox("File")
        file_layout = QFormLayout(file_group)

        file_layout.addRow("Title:", QLabel(str(self.video.title)))
        file_layout.addRow("Filename:", QLabel(str(self.video.filename)))
        file_layout.addRow("Size:", QLabel(str(FileSize(self.video.file_size))))
        file_layout.addRow(
            "Date Modified:", QLabel(str(self.video.date_entry_modified))
        )

        layout.addWidget(file_group)

        # Video info
        video_group = QGroupBox("Video")
        video_layout = QFormLayout(video_group)

        duration = Duration(int(self.video.duration * 1_000_000))
        video_layout.addRow("Duration:", QLabel(str(duration)))
        video_layout.addRow(
            "Resolution:", QLabel(f"{self.video.width}x{self.video.height}")
        )
        video_layout.addRow(
            "Codec:",
            QLabel(str(self.video.video_codec) if self.video.video_codec else "N/A"),
        )
        video_layout.addRow(
            "Codec Description:",
            QLabel(
                str(self.video.video_codec_description)
                if self.video.video_codec_description
                else "N/A"
            ),
        )
        video_layout.addRow(
            "Container:",
            QLabel(
                str(self.video.container_format)
                if self.video.container_format
                else "N/A"
            ),
        )

        # Frame rate
        if self.video.frame_rate_den and self.video.frame_rate_den > 0:
            fps = self.video.frame_rate_num / self.video.frame_rate_den
            video_layout.addRow("Frame Rate:", QLabel(f"{fps:.2f} fps"))

        layout.addWidget(video_group)

        # Audio info
        audio_group = QGroupBox("Audio")
        audio_layout = QFormLayout(audio_group)

        audio_layout.addRow(
            "Codec:",
            QLabel(str(self.video.audio_codec) if self.video.audio_codec else "N/A"),
        )
        audio_layout.addRow(
            "Channels:",
            QLabel(str(self.video.channels) if self.video.channels else "N/A"),
        )
        audio_layout.addRow(
            "Sample Rate:",
            QLabel(f"{self.video.sample_rate} Hz" if self.video.sample_rate else "N/A"),
        )
        audio_layout.addRow(
            "Bit Rate:",
            QLabel(
                f"{self.video.audio_bit_rate} bps"
                if self.video.audio_bit_rate
                else "N/A"
            ),
        )

        layout.addWidget(audio_group)

        # Status
        status_group = QGroupBox("Status")
        status_layout = QFormLayout(status_group)

        status_layout.addRow("Found:", QLabel("Yes" if self.video.found else "No"))
        status_layout.addRow(
            "Readable:", QLabel("No" if self.video.unreadable else "Yes")
        )
        status_layout.addRow(
            "Has Thumbnail:", QLabel("Yes" if self.video.with_thumbnails else "No")
        )

        if self.video.similarity_id is not None:
            status_layout.addRow(
                "Similarity Group:", QLabel(str(self.video.similarity_id))
            )

        layout.addWidget(status_group)

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    def _create_properties_tab(self) -> QWidget:
        """Create the properties tab with editable custom properties."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        widget = QWidget()
        layout = QVBoxLayout(widget)

        if not self.prop_types:
            layout.addWidget(QLabel("No custom properties defined."))
            layout.addStretch()
            scroll.setWidget(widget)
            return scroll

        # Create a form for each property
        form_layout = QFormLayout()

        for prop_type in self.prop_types:
            prop_widget = self._create_property_widget(prop_type)
            self._property_widgets[prop_type["name"]] = prop_widget

            # Create label with type info
            ptype = prop_type["type"]
            is_multiple = prop_type["multiple"]
            enumeration = prop_type.get("enumeration")

            label_text = f"{prop_type['name']}"
            if is_multiple:
                label_text += " (multiple)"
            if enumeration:
                label_text += " [enum]"

            form_layout.addRow(f"{label_text}:", prop_widget)

        layout.addLayout(form_layout)
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    def _create_property_widget(self, prop_type: dict) -> QWidget:
        """Create a widget for editing a property based on its type."""
        ptype = prop_type["type"]  # str: "bool", "int", "float", "str"
        is_multiple = prop_type["multiple"]
        enumeration = prop_type.get("enumeration")

        # Multiple values use the special widget
        if is_multiple:
            return MultipleValuesWidget(prop_type)

        # Enumeration: use combo box
        if enumeration:
            widget = QComboBox()
            for value in enumeration:
                widget.addItem(str(value), value)
            return widget

        # Simple types
        if ptype == "bool":
            widget = QCheckBox()
            return widget
        elif ptype == "int":
            widget = QSpinBox()
            widget.setRange(-999999999, 999999999)
            return widget
        elif ptype == "float":
            widget = QLineEdit()
            widget.setPlaceholderText("Enter a number")
            return widget
        elif ptype == "str":
            widget = QLineEdit()
            return widget
        else:
            # Default to line edit
            widget = QLineEdit()
            return widget

    def _load_properties(self):
        """Load current property values into widgets."""
        if not self.database:
            return

        for prop_type in self.prop_types:
            name = prop_type["name"]
            widget = self._property_widgets.get(name)
            if not widget:
                continue

            # Get default value from defaultValues list
            default_values = prop_type.get("defaultValues", [])
            default = default_values[0] if default_values else None

            # Get current value
            value = self.video.get_property(name, default)

            ptype = prop_type["type"]  # str: "bool", "int", "float", "str"
            is_multiple = prop_type["multiple"]
            enumeration = prop_type.get("enumeration")

            # Handle multiple values widget
            if is_multiple:
                widget.set_values(value)
                continue

            # Handle enumeration combo box
            if enumeration:
                # Value could be in a list
                if isinstance(value, (list, tuple)):
                    value = value[0] if value else enumeration[0]
                # Find the index
                index = widget.findData(value)
                if index >= 0:
                    widget.setCurrentIndex(index)
                continue

            # Handle simple types
            # If value is a list, extract first element
            if isinstance(value, (list, tuple)):
                value = value[0] if value else None

            if ptype == "bool":
                widget.setChecked(bool(value))
            elif ptype == "int":
                widget.setValue(int(value) if value is not None else 0)
            elif ptype == "float":
                widget.setText(str(value) if value is not None else "")
            elif ptype == "str":
                widget.setText(str(value) if value else "")
            else:
                widget.setText(str(value) if value else "")

    def _on_accept(self):
        """Save changes and close dialog."""
        if not self.database:
            self.accept()
            return

        changes = {}

        for prop_type in self.prop_types:
            name = prop_type["name"]
            widget = self._property_widgets.get(name)
            if not widget:
                continue

            # Get default value from defaultValues list
            default_values = prop_type.get("defaultValues", [])
            default = default_values[0] if default_values else None

            ptype = prop_type["type"]  # str: "bool", "int", "float", "str"
            is_multiple = prop_type["multiple"]
            enumeration = prop_type.get("enumeration")

            try:
                # Multiple values widget
                if is_multiple:
                    new_value = widget.get_values()
                # Enumeration combo box
                elif enumeration:
                    new_value = widget.currentData()
                # Simple types
                elif ptype == "bool":
                    new_value = widget.isChecked()
                elif ptype == "int":
                    new_value = widget.value()
                elif ptype == "float":
                    text = widget.text().strip()
                    new_value = float(text) if text else default
                elif ptype == "str":
                    new_value = widget.text()
                else:
                    new_value = widget.text()

                # Get current value to check if changed
                current = self.video.get_property(name, default)
                if new_value != current:
                    changes[name] = new_value

            except (ValueError, TypeError):
                # Skip invalid values
                pass

        # Apply changes
        if changes:
            # video_entry_set_tags expects {prop_name: values} where values is a list
            properties = {}
            for name, value in changes.items():
                if isinstance(value, list):
                    properties[name] = value
                else:
                    properties[name] = [value]
            self.database.video_entry_set_tags(self.video.video_id, properties)

        self.accept()
