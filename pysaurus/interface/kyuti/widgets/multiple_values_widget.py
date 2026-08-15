"""Editor for a property holding multiple values."""

from collections.abc import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.language import say
from pysaurus.interface.common.common import Uniconst
from pysaurus.interface.kyuti.widgets.elided_label import ElidedLabel
from pysaurus.interface.kyuti.widgets.entry_row import make_row_button
from pysaurus.properties.properties import PropType

MODIFIED_COLOR = "#0055cc"


class NonSubmittingLineEdit(QLineEdit):
    """QLineEdit that doesn't propagate Enter key to parent dialog."""

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Emit returnPressed but don't propagate to parent
            self.returnPressed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


class ValueRow(QWidget):
    """One value of a free-form list, with its own remove button.

    The button comes first so it stays visible however long the value is, and
    the value itself is elided rather than pushing the row out of the viewport.
    """

    def __init__(self, value, on_remove: Callable, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 1, 2, 1)
        layout.setSpacing(3)

        text = str(value)

        self.remove_button = make_row_button(
            Uniconst.CROSS, say("Remove"), value, on_remove
        )
        layout.addWidget(self.remove_button)

        self.label = ElidedLabel(text)
        self.label.setToolTip(text)
        layout.addWidget(self.label, 1)

    def set_modified(self, modified: bool):
        """Color the value when it differs from the initial ones."""
        self.label.setStyleSheet(f"color: {MODIFIED_COLOR};" if modified else "")


class MultipleValuesWidget(QWidget):
    """Widget for editing multiple values of a property.

    An enumeration gets one checkbox per allowed value; a free-form property
    gets a list where each row carries its own remove button.

    ``track_changes`` adds a Reset button and colors whatever differs from the
    values passed to ``set_values()``. Batch editing has no such initial state,
    so it opts out.
    """

    def __init__(self, prop_type: PropType, parent=None, track_changes: bool = True):
        super().__init__(parent)
        self.prop_type = prop_type
        self.ptype = prop_type.type
        self.enumeration = prop_type.enumeration
        self.track_changes = track_changes
        self._initial_values: list = []

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
                if self.track_changes:
                    cb.clicked.connect(self._update_enum_styles)
                self.checkboxes[str(value)] = cb
                layout.addWidget(cb)

            layout.addLayout(self._build_bottom_buttons(say("Uncheck all values")))
        else:
            # Free-form: one removable row per value, plus an input to add more
            self.list_widget = QListWidget()
            self.list_widget.setMaximumHeight(120)
            self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
            self.list_widget.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            layout.addWidget(self.list_widget)

            # Input row
            input_layout = QHBoxLayout()
            input_layout.setContentsMargins(0, 0, 0, 0)

            self.input_edit = NonSubmittingLineEdit()
            self.input_edit.setPlaceholderText(say("Enter value..."))
            self.input_edit.returnPressed.connect(self._add_value)
            input_layout.addWidget(self.input_edit)

            btn_add = QPushButton("+")
            btn_add.setFixedWidth(30)
            btn_add.setToolTip(say("Add value"))
            btn_add.clicked.connect(self._add_value)
            input_layout.addWidget(btn_add)

            layout.addLayout(input_layout)

            layout.addLayout(self._build_bottom_buttons(say("Remove all values")))

    def _build_bottom_buttons(self, clear_tooltip: str) -> QHBoxLayout:
        """Build the Reset/Clear row shared by both modes."""
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)

        if self.track_changes:
            btn_reset = QPushButton(say("Reset"))
            btn_reset.setToolTip(say("Restore initial values"))
            btn_reset.clicked.connect(self._reset_values)
            btn_layout.addWidget(btn_reset)

        btn_clear = QPushButton(say("Clear"))
        btn_clear.setToolTip(clear_tooltip)
        btn_clear.clicked.connect(self._clear_values)
        btn_layout.addWidget(btn_clear)

        btn_layout.addStretch()
        return btn_layout

    def _append_row(self, value):
        """Add a row displaying ``value`` at the end of the list."""
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, value)
        self.list_widget.addItem(item)

        row = ValueRow(value, self._on_remove_clicked)
        row.set_modified(self.track_changes and value not in set(self._initial_values))
        # Zero width: the row then spans the viewport instead of asking for the
        # full width of its value, which would bring a horizontal scrollbar.
        item.setSizeHint(QSize(0, row.sizeHint().height()))
        self.list_widget.setItemWidget(item, row)

    def _on_remove_clicked(self):
        """Remove the value whose cross was clicked."""
        self._remove_value(self.sender().property("value"))

    def _remove_value(self, value):
        """Remove the row holding ``value``, if any (values are unique here)."""
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).data(Qt.ItemDataRole.UserRole) == value:
                self.list_widget.takeItem(i)
                return

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

            self._append_row(value)
            self.input_edit.clear()
        except ValueError:
            pass  # Invalid input

    def _reset_values(self):
        """Reset to initial values."""
        self._set_values_internal(self._initial_values)

    def _clear_values(self):
        """Clear all values."""
        if self.enumeration:
            for cb in self.checkboxes.values():
                cb.setChecked(False)
            self._update_enum_styles()
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
            self._update_enum_styles()
        else:
            self.list_widget.clear()
            for value in values:
                self._append_row(value)

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

    def _update_enum_styles(self):
        """Color checkboxes when their state differs from initial."""
        initial_set = set(str(v) for v in self._initial_values)
        for key, cb in self.checkboxes.items():
            modified = self.track_changes and cb.isChecked() != (key in initial_set)
            cb.setStyleSheet(
                f"QCheckBox {{ color: {MODIFIED_COLOR}; }}" if modified else ""
            )

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
