"""
Dialog for batch editing properties of multiple videos.
"""

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.language import say
from pysaurus.interface.kyuti.widgets.bool_value_widget import BoolValueWidget
from pysaurus.interface.kyuti.widgets.multiple_values_widget import MultipleValuesWidget
from pysaurus.properties.properties import PropType


class BatchEditDialog(QDialog):
    """
    Dialog for editing properties of multiple videos at once.

    Shows a form with all custom properties. For each property:
    - A checkbox to indicate whether to apply the change
    - An appropriate input widget based on the property type
    """

    def __init__(
        self, video_ids: list[int], prop_types: list[PropType], ctx, parent=None
    ):
        super().__init__(parent)
        self.video_ids = video_ids
        self.prop_types = prop_types
        self.ctx = ctx
        self._property_widgets: dict[str, tuple[QCheckBox, QWidget]] = {}

        self.setWindowTitle(
            say("Edit Properties - {count} videos", count=len(video_ids))
        )
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        # Info label
        info_label = QLabel(
            say(
                "Set properties for {count} selected videos.\n"
                "Check the box next to a property to apply the change.",
                count=len(self.video_ids),
            )
        )
        info_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(info_label)

        # Scroll area for properties
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        widget = QWidget()
        form_layout = QVBoxLayout(widget)

        if not self.prop_types:
            form_layout.addWidget(QLabel(say("No custom properties defined.")))
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
            assert isinstance(button, QPushButton)
            button.setAutoDefault(False)
            button.setDefault(False)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_property_group(self, prop_type: PropType) -> QGroupBox:
        """Create a group box for a property with checkbox and input."""
        group = QGroupBox()
        layout = QHBoxLayout(group)

        name = prop_type.name
        ptype = prop_type.type  # str: "bool", "int", "float", "str"
        is_multiple = prop_type.multiple
        enumeration = prop_type.enumeration
        default_values = prop_type.default
        default = default_values[0] if default_values else None

        # Build label with type info
        label_text = name
        if is_multiple:
            label_text += " (" + say("multiple") + ")"
        if enumeration:
            label_text += " [" + say("enum") + "]"

        # Checkbox to enable/disable the property change
        checkbox = QCheckBox(f"{label_text}:")
        checkbox.setToolTip(
            say("Check to set {name} for all selected videos", name=name)
        )
        layout.addWidget(checkbox)

        # Create the appropriate input widget based on type
        if is_multiple:
            # No initial state to compare against here: the checkbox on the left
            # says whether the property is touched at all.
            input_widget = MultipleValuesWidget(prop_type, track_changes=False)
            input_widget.setEnabled(False)
        elif enumeration:
            input_widget = QComboBox()
            for value in enumeration:
                input_widget.addItem(str(value), value)
            input_widget.setEnabled(False)
        elif ptype == "bool":
            # No "not set" state here: the checkbox on the left already says
            # whether this property is touched at all.
            input_widget = BoolValueWidget(with_undefined=False)
            # default is typed as PropUnitType; on a bool property it is a bool,
            # and a missing one starts the widget on False either way.
            input_widget.set_value(bool(default))
            input_widget.setEnabled(False)
        elif ptype == "int":
            input_widget = QSpinBox()
            input_widget.setRange(-999999999, 999999999)
            input_widget.setValue(int(default) if default is not None else 0)
            input_widget.setEnabled(False)
        elif ptype == "float":
            input_widget = QLineEdit()
            input_widget.setPlaceholderText(say("Enter a number"))
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
        if not self.ctx.has_database():
            self.accept()
            return

        changes = {}

        for prop_type in self.prop_types:
            name = prop_type.name
            checkbox, widget = self._property_widgets.get(name, (None, None))
            if not checkbox or not checkbox.isChecked():
                continue

            ptype = prop_type.type  # str: "bool", "int", "float", "str"
            is_multiple = prop_type.multiple
            enumeration = prop_type.enumeration
            default_values = prop_type.default
            default = default_values[0] if default_values else None

            try:
                if is_multiple:
                    assert isinstance(widget, MultipleValuesWidget)
                    new_value = widget.get_values()
                elif enumeration:
                    assert isinstance(widget, QComboBox)
                    new_value = widget.currentData()
                elif ptype == "bool":
                    assert isinstance(widget, BoolValueWidget)
                    new_value = widget.value()
                elif ptype == "int":
                    assert isinstance(widget, QSpinBox)
                    new_value = widget.value()
                elif ptype == "float":
                    assert isinstance(widget, QLineEdit)
                    text = widget.text().strip()
                    new_value = float(text) if text else default
                elif ptype == "str":
                    assert isinstance(widget, QLineEdit)
                    new_value = widget.text()
                else:
                    assert isinstance(widget, QLineEdit)
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
                self.ctx.set_video_properties(video_id, properties)

        self.accept()
