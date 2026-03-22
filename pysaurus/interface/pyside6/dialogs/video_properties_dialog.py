"""
Dialog for viewing and editing video properties.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent

from pysaurus.properties.properties import PropType
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

    def __init__(self, prop_type: PropType, parent=None):
        super().__init__(parent)
        self.prop_type = prop_type
        self.ptype = prop_type.type
        self.enumeration = prop_type.enumeration
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

    def __init__(
        self, video: VideoPattern, prop_types: list[PropType], ctx, parent=None
    ):
        super().__init__(parent)
        self.video = video
        self.prop_types = prop_types
        self.ctx = ctx
        self._property_widgets: dict[str, QWidget] = {}
        self._clear_buttons: dict[str, QPushButton] = {}
        self._initially_defined: dict[str, bool] = {}
        self._cleared: set[str] = set()
        self._user_modified: set[str] = set()
        self._loading = False

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

        # Properties tab
        props_tab = self._create_properties_tab()
        tabs.addTab(props_tab, "Properties")

        # Info tab
        info_tab = self._create_info_tab()
        tabs.addTab(info_tab, "Info")

        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        # Disable auto-default to prevent ENTER from submitting the form
        for button in self.button_box.buttons():
            button.setAutoDefault(False)
            button.setDefault(False)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

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
        if self.video.similarity_id_reencoded is not None:
            status_layout.addRow(
                "Re-encoded Group:", QLabel(str(self.video.similarity_id_reencoded))
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
            name = prop_type.name

            # Create label with type info
            label_text = name
            if prop_type.multiple:
                label_text += " (multiple)"
            if prop_type.enumeration:
                label_text += " [enum]"

            if prop_type.multiple:
                prop_widget = MultipleValuesWidget(prop_type)
                self._property_widgets[name] = prop_widget
                form_layout.addRow(f"{label_text}:", prop_widget)
            else:
                # Single property: input widget + Clear button
                container = QWidget()
                h_layout = QHBoxLayout(container)
                h_layout.setContentsMargins(0, 0, 0, 0)
                h_layout.setSpacing(4)

                input_widget = self._create_single_property_widget(prop_type)
                h_layout.addWidget(input_widget, 1)

                clear_btn = QPushButton("Clear")
                clear_btn.setToolTip(f"Remove {name} value from this video")
                clear_btn.setFixedWidth(50)
                clear_btn.clicked.connect(
                    lambda _checked, n=name: self._on_clear_property(n)
                )
                clear_btn.setVisible(False)
                h_layout.addWidget(clear_btn)

                self._property_widgets[name] = input_widget
                self._clear_buttons[name] = clear_btn
                form_layout.addRow(f"{label_text}:", container)

        layout.addLayout(form_layout)
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    def _create_single_property_widget(self, prop_type: PropType) -> QWidget:
        """Create input widget for a single-value property, with change signal."""
        name = prop_type.name
        ptype = prop_type.type

        if prop_type.enumeration:
            widget = QComboBox()
            for value in prop_type.enumeration:
                widget.addItem(str(value), value)
            widget.activated.connect(lambda _idx, n=name: self._on_widget_changed(n))
            return widget

        if ptype == "bool":
            widget = QCheckBox()
            widget.clicked.connect(lambda _checked, n=name: self._on_widget_changed(n))
            return widget
        if ptype == "int":
            widget = QSpinBox()
            widget.setRange(-999999999, 999999999)
            widget.valueChanged.connect(lambda _val, n=name: self._on_widget_changed(n))
            return widget
        # float or str
        widget = QLineEdit()
        if ptype == "float":
            widget.setPlaceholderText("Enter a number")
        widget.textEdited.connect(lambda _text, n=name: self._on_widget_changed(n))
        return widget

    def _on_widget_changed(self, name: str):
        """Handle user modification of a single property widget."""
        if self._loading:
            return
        self._user_modified.add(name)
        self._cleared.discard(name)
        self._update_prop_style(name)

    def _on_clear_property(self, name: str):
        """Handle Clear button click: remove the property value."""
        self._cleared.add(name)
        self._user_modified.discard(name)

        # Reset widget to default value
        prop_type = next(pt for pt in self.prop_types if pt.name == name)
        default_values = prop_type.default
        default = default_values[0] if default_values else None
        widget = self._property_widgets[name]

        self._loading = True
        try:
            if prop_type.enumeration:
                index = widget.findData(default) if default is not None else 0
                widget.setCurrentIndex(max(index, 0))
            elif prop_type.type == "bool":
                widget.setChecked(bool(default) if default is not None else False)
            elif prop_type.type == "int":
                widget.setValue(int(default) if default is not None else 0)
            elif prop_type.type == "float":
                widget.setText(str(default) if default is not None else "")
            else:
                widget.setText(str(default) if default else "")
        finally:
            self._loading = False

        self._update_prop_style(name)

    def _update_prop_style(self, name: str):
        """Update italic style and Clear button visibility for a single property."""
        widget = self._property_widgets.get(name)
        if not widget:
            return

        is_defined = self._initially_defined.get(name, False)
        is_cleared = name in self._cleared
        is_modified = name in self._user_modified

        # Italic when showing default value (not explicitly set)
        use_italic = is_cleared or (not is_defined and not is_modified)
        font = widget.font()
        font.setItalic(use_italic)
        widget.setFont(font)

        # Clear button visible when a value would be saved
        clear_btn = self._clear_buttons.get(name)
        if clear_btn:
            clear_btn.setVisible(not is_cleared and (is_defined or is_modified))

    def _read_widget_value(self, prop_type: PropType, widget: QWidget):
        """Read the current value from a property widget."""
        ptype = prop_type.type
        if prop_type.multiple:
            return widget.get_values()
        if prop_type.enumeration:
            return widget.currentData()
        if ptype == "bool":
            return widget.isChecked()
        if ptype == "int":
            return widget.value()
        if ptype == "float":
            text = widget.text().strip()
            default_values = prop_type.default
            default = default_values[0] if default_values else None
            return float(text) if text else default
        return widget.text()

    def _load_properties(self):
        """Load current property values into widgets."""
        self._initial_widget_values: dict = {}

        if not self.ctx.has_database():
            return

        video_properties = getattr(self.video, "properties", {}) or {}

        self._loading = True
        try:
            for prop_type in self.prop_types:
                name = prop_type.name
                widget = self._property_widgets.get(name)
                if not widget:
                    continue

                # Track if property is explicitly defined on this video
                prop_values = video_properties.get(name)
                is_defined = prop_values is not None and len(prop_values) > 0
                self._initially_defined[name] = is_defined

                # Get default value from default list
                default_values = prop_type.default
                default = default_values[0] if default_values else None

                # Get current value
                value = self.video.get_property(name, default)

                ptype = prop_type.type
                is_multiple = prop_type.multiple
                enumeration = prop_type.enumeration

                # Handle multiple values widget
                if is_multiple:
                    widget.set_values(value)
                    self._initial_widget_values[name] = self._read_widget_value(
                        prop_type, widget
                    )
                    continue

                # Handle enumeration combo box
                if enumeration:
                    if isinstance(value, (list, tuple)):
                        value = value[0] if value else enumeration[0]
                    index = widget.findData(value)
                    if index >= 0:
                        widget.setCurrentIndex(index)
                elif isinstance(value, (list, tuple)):
                    value = value[0] if value else None

                # Handle simple types
                if not enumeration:
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

                self._initial_widget_values[name] = self._read_widget_value(
                    prop_type, widget
                )
                self._update_prop_style(name)
        finally:
            self._loading = False

    def _on_accept(self):
        """Save changes and close dialog."""
        if not self.ctx.has_database():
            self.accept()
            return

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setEnabled(False)

        # {prop_name: [values]} to send to backend
        properties = {}

        for prop_type in self.prop_types:
            name = prop_type.name
            widget = self._property_widgets.get(name)
            if not widget:
                continue

            # Cleared single property: send empty list to delete
            if name in self._cleared:
                if self._initially_defined.get(name, False):
                    properties[name] = []
                continue

            try:
                new_value = self._read_widget_value(prop_type, widget)
                initial = self._initial_widget_values.get(name)
                if new_value != initial:
                    if isinstance(new_value, list):
                        properties[name] = new_value
                    else:
                        properties[name] = [new_value]
            except (ValueError, TypeError):
                pass

        if properties:
            self.ctx.set_video_properties(self.video.video_id, properties)

        self.accept()
