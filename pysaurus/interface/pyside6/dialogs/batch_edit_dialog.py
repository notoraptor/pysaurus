"""
Dialog for batch editing properties of multiple videos.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


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
        self._buttons: list[QPushButton] = []  # Track buttons for enabling/disabling

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

            btn_clear = QPushButton("Clear")
            btn_clear.setToolTip("Uncheck all values")
            btn_clear.clicked.connect(self._clear_values)
            btn_layout.addWidget(btn_clear)
            self._buttons.append(btn_clear)

            btn_layout.addStretch()
            layout.addLayout(btn_layout)
        else:
            # Free-form: show list with add/remove buttons
            self.list_widget = QListWidget()
            self.list_widget.setMaximumHeight(80)
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
            self._buttons.append(btn_add)

            btn_remove = QPushButton("-")
            btn_remove.setFixedWidth(30)
            btn_remove.setToolTip("Remove selected value(s)")
            btn_remove.clicked.connect(self._remove_selected)
            input_layout.addWidget(btn_remove)
            self._buttons.append(btn_remove)

            layout.addLayout(input_layout)

            # Buttons row
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 0, 0, 0)

            btn_clear = QPushButton("Clear")
            btn_clear.setToolTip("Remove all values")
            btn_clear.clicked.connect(self._clear_values)
            btn_layout.addWidget(btn_clear)
            self._buttons.append(btn_clear)

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
        selected = self.list_widget.selectedItems()
        for item in selected:
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)

    def _clear_values(self):
        """Clear all values."""
        if self.enumeration:
            for cb in self.checkboxes.values():
                cb.setChecked(False)
        else:
            self.list_widget.clear()

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

    def setEnabled(self, enabled: bool):
        """Enable or disable the widget."""
        super().setEnabled(enabled)
        if self.enumeration:
            for cb in self.checkboxes.values():
                cb.setEnabled(enabled)
        else:
            self.list_widget.setEnabled(enabled)
            self.input_edit.setEnabled(enabled)
        for btn in self._buttons:
            btn.setEnabled(enabled)


class BatchEditDialog(QDialog):
    """
    Dialog for editing properties of multiple videos at once.

    Shows a form with all custom properties. For each property:
    - A checkbox to indicate whether to apply the change
    - An appropriate input widget based on the property type
    """

    def __init__(self, video_ids: list[int], prop_types: list, database, parent=None):
        super().__init__(parent)
        self.video_ids = video_ids
        self.prop_types = prop_types
        self.database = database
        self._property_widgets: dict[str, tuple[QCheckBox, QWidget]] = {}

        self.setWindowTitle(f"Edit Properties - {len(video_ids)} videos")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        # Info label
        info_label = QLabel(
            f"Set properties for {len(self.video_ids)} selected videos.\n"
            "Check the box next to a property to apply the change."
        )
        info_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(info_label)

        # Scroll area for properties
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        widget = QWidget()
        form_layout = QVBoxLayout(widget)

        if not self.prop_types:
            form_layout.addWidget(QLabel("No custom properties defined."))
        else:
            # Create a form for each property
            for prop_type in self.prop_types:
                prop_group = self._create_property_group(prop_type)
                form_layout.addWidget(prop_group)

        form_layout.addStretch()
        scroll.setWidget(widget)
        layout.addWidget(scroll)

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

    def _create_property_group(self, prop_type: dict) -> QGroupBox:
        """Create a group box for a property with checkbox and input."""
        group = QGroupBox()
        layout = QHBoxLayout(group)

        name = prop_type["name"]
        ptype = prop_type["type"]  # str: "bool", "int", "float", "str"
        is_multiple = prop_type["multiple"]
        enumeration = prop_type.get("enumeration")
        default_values = prop_type.get("defaultValues", [])
        default = default_values[0] if default_values else None

        # Build label with type info
        label_text = name
        if is_multiple:
            label_text += " (multiple)"
        if enumeration:
            label_text += " [enum]"

        # Checkbox to enable/disable the property change
        checkbox = QCheckBox(f"{label_text}:")
        checkbox.setToolTip(f"Check to set {name} for all selected videos")
        layout.addWidget(checkbox)

        # Create the appropriate input widget based on type
        if is_multiple:
            input_widget = MultipleValuesWidget(prop_type)
            input_widget.setEnabled(False)
        elif enumeration:
            input_widget = QComboBox()
            for value in enumeration:
                input_widget.addItem(str(value), value)
            input_widget.setEnabled(False)
        elif ptype == "bool":
            input_widget = QCheckBox("Yes")
            input_widget.setEnabled(False)
        elif ptype == "int":
            input_widget = QSpinBox()
            input_widget.setRange(-999999999, 999999999)
            input_widget.setValue(int(default) if default is not None else 0)
            input_widget.setEnabled(False)
        elif ptype == "float":
            input_widget = QLineEdit()
            input_widget.setPlaceholderText("Enter a number")
            if default is not None:
                input_widget.setText(str(default))
            input_widget.setEnabled(False)
        elif ptype == "str":
            input_widget = QLineEdit()
            if default:
                input_widget.setText(str(default))
            input_widget.setEnabled(False)
        else:
            input_widget = QLineEdit()
            input_widget.setEnabled(False)

        layout.addWidget(input_widget, 1)

        # Connect checkbox to enable/disable input
        checkbox.toggled.connect(input_widget.setEnabled)

        # Store the widgets
        self._property_widgets[name] = (checkbox, input_widget)

        return group

    def _on_accept(self):
        """Apply changes and close dialog."""
        if not self.database:
            self.accept()
            return

        changes = {}

        for prop_type in self.prop_types:
            name = prop_type["name"]
            checkbox, widget = self._property_widgets.get(name, (None, None))
            if not checkbox or not checkbox.isChecked():
                continue

            ptype = prop_type["type"]  # str: "bool", "int", "float", "str"
            is_multiple = prop_type["multiple"]
            enumeration = prop_type.get("enumeration")
            default_values = prop_type.get("defaultValues", [])
            default = default_values[0] if default_values else None

            try:
                if is_multiple:
                    new_value = widget.get_values()
                elif enumeration:
                    new_value = widget.currentData()
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

                changes[name] = new_value

            except (ValueError, TypeError):
                # Skip invalid values
                pass

        # Apply changes to all selected videos
        if changes:
            # video_entry_set_tags expects {prop_name: values} where values is a list
            properties = {}
            for name, value in changes.items():
                if isinstance(value, list):
                    properties[name] = value
                else:
                    properties[name] = [value]

            for video_id in self.video_ids:
                self.database.video_entry_set_tags(video_id, properties)

        self.accept()
