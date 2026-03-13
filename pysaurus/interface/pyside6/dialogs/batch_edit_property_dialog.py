"""
Dialog for batch editing a single property of multiple videos.

Three-column layout similar to web interface:
- To remove (left)
- Current values with counts (center)
- To add (right)

Each entry has inline action buttons (left of text).
Bottom of each column has bulk action buttons.
"""

from PySide6.QtCore import Qt

from pysaurus.properties.properties import PropType
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

_BTN_STYLE = (
    "QPushButton { padding: 1px 5px; min-width: 20px; }"
    "QPushButton:hover { background-color: #0078d4; color: white; }"
)


def _make_entry_widget(
    label_text: str, value, buttons: list[tuple[str, str, callable]]
):
    """Create a row widget with action buttons on the left and a label.

    Args:
        label_text: Text to display.
        value: Value to store on each button (retrieved via sender().property("value")).
        buttons: List of (text, tooltip, slot) for each button.
            slot must be a bound method (not a lambda) to avoid PySide6 GC.
    """
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(2, 1, 2, 1)
    layout.setSpacing(3)
    for text, tooltip, slot in buttons:
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setStyleSheet(_BTN_STYLE)
        btn.setFixedWidth(24)
        btn.setProperty("value", value)
        btn.clicked.connect(slot)
        layout.addWidget(btn)
    label = QLabel(label_text)
    label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    layout.addWidget(label, 1)
    return widget


class _EntryList(QScrollArea):
    """Scrollable list of entry widgets with a count() method."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch()
        self.setWidget(self._container)
        self._count = 0

    def clear(self):
        """Remove all entry widgets."""
        # Remove all widgets except the trailing stretch
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._count = 0

    def add_entry(self, widget: QWidget):
        """Add an entry widget before the trailing stretch."""
        self._layout.insertWidget(self._count, widget)
        self._count += 1

    def count(self) -> int:
        """Return the number of entries."""
        return self._count


class BatchEditPropertyDialog(QDialog):
    """
    Dialog for editing a property across multiple selected videos.

    Shows three columns:
    - Left: values to remove from videos
    - Center: current values (with count of videos having each value)
    - Right: values to add to videos
    """

    def __init__(
        self,
        prop_name: str,
        prop_type: PropType,
        nb_videos: int,
        values_and_counts: list,
        parent=None,
    ):
        super().__init__(parent)
        self.prop_name = prop_name
        self.prop_type = prop_type
        self.ptype = prop_type.type
        self.is_multiple = prop_type.multiple
        self.enumeration = prop_type.enumeration
        self.nb_videos = nb_videos

        # Build value -> count mapping
        self._value_counts: dict = {}
        for item in values_and_counts:
            value, count = item[0], item[1]
            self._value_counts[value] = count

        # Track changes
        self._to_add: list = []
        self._to_remove: list = []
        self._current: list = list(self._value_counts.keys())

        self.setWindowTitle(f'Edit "{prop_name}" for {nb_videos} video(s)')
        self.setMinimumWidth(700)
        self.setMinimumHeight(400)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        # Header labels
        header_layout = QHBoxLayout()
        header_layout.addWidget(
            QLabel("<b>To remove</b>"), 1, Qt.AlignmentFlag.AlignCenter
        )
        header_layout.addWidget(
            QLabel("<b>Current values</b>"), 1, Qt.AlignmentFlag.AlignCenter
        )
        header_layout.addWidget(
            QLabel("<b>To add</b>"), 1, Qt.AlignmentFlag.AlignCenter
        )
        layout.addLayout(header_layout)

        # Three columns
        columns_layout = QHBoxLayout()

        # Left column: to remove
        left_layout = QVBoxLayout()
        self.remove_list = _EntryList()
        left_layout.addWidget(self.remove_list)
        btn_restore_all = QPushButton("Restore All →")
        btn_restore_all.setToolTip("Restore all removed values back to current")
        btn_restore_all.clicked.connect(self._restore_all)
        left_layout.addWidget(btn_restore_all)
        columns_layout.addLayout(left_layout, 1)

        # Center column: current values
        center_layout = QVBoxLayout()
        self.current_list = _EntryList()
        center_layout.addWidget(self.current_list)
        bulk_center = QHBoxLayout()
        btn_remove_all = QPushButton("← Remove All")
        btn_remove_all.setToolTip("Move all current values to remove list")
        btn_remove_all.clicked.connect(self._move_all_to_remove)
        bulk_center.addWidget(btn_remove_all)
        if self.is_multiple:
            btn_add_all = QPushButton("Add All →")
            btn_add_all.setToolTip("Move all current values to add list")
            btn_add_all.clicked.connect(self._move_all_to_add)
            bulk_center.addWidget(btn_add_all)
        center_layout.addLayout(bulk_center)
        columns_layout.addLayout(center_layout, 1)

        # Right column: to add
        right_layout = QVBoxLayout()
        self.add_list = _EntryList()
        right_layout.addWidget(self.add_list)
        btn_cancel_all = QPushButton("← Cancel All")
        btn_cancel_all.setToolTip("Cancel all additions")
        btn_cancel_all.clicked.connect(self._cancel_all)
        right_layout.addWidget(btn_cancel_all)
        columns_layout.addLayout(right_layout, 1)

        layout.addLayout(columns_layout)

        # New value input (adapted to property type)
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("New value:"))

        if self.enumeration:
            self.value_input = QComboBox()
            self.value_input.addItems([str(v) for v in self.enumeration])
            input_layout.addWidget(self.value_input, 1)
        elif self.ptype == "bool":
            self.value_input = QComboBox()
            self.value_input.addItems(["true", "false"])
            input_layout.addWidget(self.value_input, 1)
        elif self.ptype == "int":
            self.value_input = QSpinBox()
            self.value_input.setRange(-2_147_483_648, 2_147_483_647)
            input_layout.addWidget(self.value_input, 1)
        elif self.ptype == "float":
            self.value_input = QDoubleSpinBox()
            self.value_input.setRange(-1e15, 1e15)
            self.value_input.setDecimals(6)
            input_layout.addWidget(self.value_input, 1)
        else:
            self.value_input = QLineEdit()
            self.value_input.setPlaceholderText("Enter new value...")
            self.value_input.returnPressed.connect(self._add_new_value)
            input_layout.addWidget(self.value_input, 1)

        btn_add_new = QPushButton("Add")
        btn_add_new.clicked.connect(self._add_new_value)
        input_layout.addWidget(btn_add_new)

        layout.addLayout(input_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Initial population
        self._refresh_lists()

    # =========================================================================
    # List population with inline buttons
    # =========================================================================

    def _refresh_lists(self):
        """Refresh all three lists."""
        self._populate_remove_list()
        self._populate_current_list()
        self._populate_add_list()

    def _populate_remove_list(self):
        """Populate the remove list with restore buttons."""
        self.remove_list.clear()
        for value in self._to_remove:
            count = self._value_counts.get(value, 0)
            widget = _make_entry_widget(
                f"{value} ({count})",
                value,
                [("→", "Restore to current", self._on_restore_clicked)],
            )
            self.remove_list.add_entry(widget)

    def _populate_current_list(self):
        """Populate the current values list with remove/add buttons."""
        self.current_list.clear()
        for value in self._current:
            count = self._value_counts.get(value, 0)
            widget = _make_entry_widget(
                f"{value} ({count})",
                value,
                [
                    ("←", "Remove", self._on_remove_clicked),
                    ("→", "Add", self._on_add_clicked),
                ],
            )
            self.current_list.add_entry(widget)

    def _populate_add_list(self):
        """Populate the add list with cancel buttons."""
        self.add_list.clear()
        for value in self._to_add:
            count = self._value_counts.get(value, 0)
            label = f"{value} ({count})" if count > 0 else f"{value} (new)"
            widget = _make_entry_widget(
                label, value, [("←", "Cancel", self._on_cancel_clicked)]
            )
            self.add_list.add_entry(widget)

    # =========================================================================
    # Button click handlers (use self.sender() to avoid lambda GC)
    # =========================================================================

    def _on_remove_clicked(self):
        self._remove_one(self.sender().property("value"))

    def _on_add_clicked(self):
        self._add_one(self.sender().property("value"))

    def _on_restore_clicked(self):
        self._restore_one(self.sender().property("value"))

    def _on_cancel_clicked(self):
        self._cancel_one(self.sender().property("value"))

    # =========================================================================
    # Single-item actions (inline buttons)
    # =========================================================================

    def _remove_one(self, value):
        """Move a single value from current to remove."""
        if value in self._current:
            self._current.remove(value)
            self._to_remove.append(value)
            self._refresh_lists()

    def _add_one(self, value):
        """Move a single value from current to add."""
        if value not in self._current:
            return
        if self.is_multiple:
            self._current.remove(value)
            self._to_add.append(value)
        else:
            # Single-value: selected value becomes the only add
            self._to_add = [value]
            self._current.clear()
            self._to_remove = [v for v in self._value_counts if v != value]
        self._refresh_lists()

    def _restore_one(self, value):
        """Restore a single value from remove to current."""
        if value in self._to_remove:
            self._to_remove.remove(value)
            self._current.append(value)
            if not self.is_multiple and self._current:
                self._to_add.clear()
            self._refresh_lists()

    def _cancel_one(self, value):
        """Cancel a single value from add list."""
        if value in self._to_add:
            self._to_add.remove(value)
            if value in self._value_counts:
                self._current.append(value)
            if not self.is_multiple and not self._to_add:
                for v in self._to_remove:
                    self._current.append(v)
                self._to_remove.clear()
            self._refresh_lists()

    # =========================================================================
    # Bulk actions (bottom buttons)
    # =========================================================================

    def _restore_all(self):
        """Restore all removed values back to current."""
        for value in self._to_remove:
            self._current.append(value)
        self._to_remove.clear()
        if not self.is_multiple and self._current:
            self._to_add.clear()
        self._refresh_lists()

    def _move_all_to_remove(self):
        """Move all current values to remove list."""
        for value in self._current:
            self._to_remove.append(value)
        self._current.clear()
        self._refresh_lists()

    def _move_all_to_add(self):
        """Move all current values to add list (multiple-value properties only)."""
        for value in self._current:
            self._to_add.append(value)
        self._current.clear()
        self._refresh_lists()

    def _cancel_all(self):
        """Cancel all additions."""
        for value in self._to_add:
            if value in self._value_counts:
                self._current.append(value)
        self._to_add.clear()
        if not self.is_multiple:
            for value in self._to_remove:
                self._current.append(value)
            self._to_remove.clear()
        self._refresh_lists()

    # =========================================================================
    # New value input
    # =========================================================================

    def _add_new_value(self):
        """Add a new value to the add list."""
        try:
            if isinstance(self.value_input, QComboBox):
                text = self.value_input.currentText().strip()
                if not text:
                    return
                if self.ptype == "bool":
                    value = text == "true"
                elif self.ptype == "int":
                    value = int(text)
                elif self.ptype == "float":
                    value = float(text)
                else:
                    value = text
            elif isinstance(self.value_input, QSpinBox):
                value = self.value_input.value()
            elif isinstance(self.value_input, QDoubleSpinBox):
                value = self.value_input.value()
            else:
                text = self.value_input.text().strip()
                if not text:
                    return
                value = text

            # Don't add duplicates
            if value in self._to_add or value in self._current:
                return

            if self.is_multiple:
                # If value was previously removed, restore it instead
                if value in self._to_remove:
                    self._to_remove.remove(value)
                    self._current.append(value)
                else:
                    self._to_add.append(value)
            else:
                # Single-value: new value replaces everything
                self._to_add = [value]
                self._current.clear()
                self._to_remove = list(self._value_counts.keys())

            self._refresh_lists()

        except ValueError:
            pass  # Invalid input

    # =========================================================================
    # Result
    # =========================================================================

    def get_changes(self) -> tuple[list, list]:
        """
        Get the changes to apply.

        Returns:
            Tuple of (values_to_add, values_to_remove)
        """
        return (self._to_add, self._to_remove)

    @staticmethod
    def edit_property(
        prop_name: str,
        prop_type: PropType,
        nb_videos: int,
        values_and_counts: list,
        parent=None,
    ) -> tuple[list, list] | None:
        """
        Show dialog and return changes.

        Returns:
            Tuple of (add, remove) lists, or None if cancelled
        """
        dialog = BatchEditPropertyDialog(
            prop_name, prop_type, nb_videos, values_and_counts, parent
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_changes()
        return None
