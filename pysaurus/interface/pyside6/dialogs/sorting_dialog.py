"""
Dialog for setting video sorting.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from pysaurus.interface.common.common import FIELD_MAP


class SortingDialog(QDialog):
    """
    Dialog for setting video sort order.

    Allows multiple sort criteria with ascending/descending order.
    """

    def __init__(
        self, current_sorting: list[tuple[str, bool]] | None = None, parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle("Set Sorting")
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)

        self._current = current_sorting or []

        self._setup_ui()
        self._load_current()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Sort by (first has highest priority):"))

        # Sort criteria list
        self.sort_list = QListWidget()
        self.sort_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        layout.addWidget(self.sort_list)

        # Buttons for managing sort criteria
        btn_layout = QHBoxLayout()

        self.btn_up = QPushButton("Move Up")
        self.btn_up.clicked.connect(self._move_up)
        btn_layout.addWidget(self.btn_up)

        self.btn_down = QPushButton("Move Down")
        self.btn_down.clicked.connect(self._move_down)
        btn_layout.addWidget(self.btn_down)

        self.btn_toggle = QPushButton("Toggle Direction")
        self.btn_toggle.clicked.connect(self._toggle_direction)
        btn_layout.addWidget(self.btn_toggle)

        self.btn_remove = QPushButton("Remove")
        self.btn_remove.clicked.connect(self._remove_selected)
        btn_layout.addWidget(self.btn_remove)

        layout.addLayout(btn_layout)

        # Add new field section
        add_layout = QHBoxLayout()

        add_layout.addWidget(QLabel("Add field:"))

        self.field_combo = QComboBox()
        for field_info in FIELD_MAP.sortable:
            self.field_combo.addItem(field_info.title, field_info.name)
        add_layout.addWidget(self.field_combo)

        self.btn_add_asc = QPushButton("Add ↑")
        self.btn_add_asc.setToolTip("Add ascending")
        self.btn_add_asc.clicked.connect(lambda: self._add_field(False))
        add_layout.addWidget(self.btn_add_asc)

        self.btn_add_desc = QPushButton("Add ↓")
        self.btn_add_desc.setToolTip("Add descending")
        self.btn_add_desc.clicked.connect(lambda: self._add_field(True))
        add_layout.addWidget(self.btn_add_desc)

        layout.addLayout(add_layout)

        # Dialog buttons
        button_box = QDialogButtonBox()
        button_box.addButton("Apply", QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton("Reset", QDialogButtonBox.ButtonRole.ResetRole)
        button_box.addButton(QDialogButtonBox.StandardButton.Cancel)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.clicked.connect(self._on_button_clicked)

        layout.addWidget(button_box)

    def _load_current(self):
        """Load current sorting settings."""
        self.sort_list.clear()
        for field, reverse in self._current:
            self._add_item(field, reverse)

    def _add_item(self, field: str, reverse: bool):
        """Add a sort criterion to the list."""
        # Get field title
        title = field
        if field in FIELD_MAP.fields:
            title = FIELD_MAP.fields[field].title

        direction = "↓" if reverse else "↑"
        text = f"{title} {direction}"

        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, (field, reverse))
        self.sort_list.addItem(item)

    def _add_field(self, reverse: bool):
        """Add a new field to the sort list."""
        field = self.field_combo.currentData()
        if field:
            self._add_item(field, reverse)

    def _move_up(self):
        """Move selected item up."""
        row = self.sort_list.currentRow()
        if row > 0:
            item = self.sort_list.takeItem(row)
            self.sort_list.insertItem(row - 1, item)
            self.sort_list.setCurrentRow(row - 1)

    def _move_down(self):
        """Move selected item down."""
        row = self.sort_list.currentRow()
        if row < self.sort_list.count() - 1:
            item = self.sort_list.takeItem(row)
            self.sort_list.insertItem(row + 1, item)
            self.sort_list.setCurrentRow(row + 1)

    def _toggle_direction(self):
        """Toggle the direction of the selected item."""
        item = self.sort_list.currentItem()
        if item:
            field, reverse = item.data(Qt.ItemDataRole.UserRole)
            reverse = not reverse

            # Update item
            title = field
            if field in FIELD_MAP.fields:
                title = FIELD_MAP.fields[field].title

            direction = "↓" if reverse else "↑"
            item.setText(f"{title} {direction}")
            item.setData(Qt.ItemDataRole.UserRole, (field, reverse))

    def _remove_selected(self):
        """Remove the selected item."""
        row = self.sort_list.currentRow()
        if row >= 0:
            self.sort_list.takeItem(row)

    def _on_button_clicked(self, button):
        """Handle button clicks."""
        role = self.sender().buttonRole(button)
        if role == QDialogButtonBox.ButtonRole.ResetRole:
            self.sort_list.clear()

    def get_sorting(self) -> list[tuple[str, bool]]:
        """Get the sorting settings as a list of (field, reverse) tuples."""
        result = []
        for i in range(self.sort_list.count()):
            item = self.sort_list.item(i)
            result.append(item.data(Qt.ItemDataRole.UserRole))
        return result
