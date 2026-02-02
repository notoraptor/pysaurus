"""
Dialog for batch editing a single property of multiple videos.

Three-column layout similar to web interface:
- To remove (left)
- Current values with counts (center)
- To add (right)
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)


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
        prop_type: dict,
        nb_videos: int,
        values_and_counts: list,
        parent=None,
    ):
        """
        Initialize the dialog.

        Args:
            prop_name: Property name
            prop_type: Property definition dict with keys like "type", "multiple", "enumeration"
            nb_videos: Number of selected videos
            values_and_counts: List of [value, count] pairs from count_property_values
            parent: Parent widget
        """
        super().__init__(parent)
        self.prop_name = prop_name
        self.prop_type = prop_type
        self.ptype = prop_type["type"]
        self.is_multiple = prop_type["multiple"]
        self.enumeration = prop_type.get("enumeration")
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
        self.remove_list = QListWidget()
        self.remove_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        left_layout.addWidget(self.remove_list)

        btn_restore = QPushButton("→ Restore")
        btn_restore.setToolTip("Move back to current")
        btn_restore.clicked.connect(self._restore_from_remove)
        left_layout.addWidget(btn_restore)

        columns_layout.addLayout(left_layout, 1)

        # Center column: current values
        center_layout = QVBoxLayout()
        self.current_list = QListWidget()
        self.current_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._populate_current_list()
        center_layout.addWidget(self.current_list)

        # Move buttons
        move_btns_layout = QHBoxLayout()
        btn_move_left = QPushButton("← Remove")
        btn_move_left.setToolTip("Mark for removal")
        btn_move_left.clicked.connect(self._move_to_remove)
        move_btns_layout.addWidget(btn_move_left)

        btn_move_right = QPushButton("Add →")
        btn_move_right.setToolTip("Mark for addition")
        btn_move_right.clicked.connect(self._move_to_add)
        move_btns_layout.addWidget(btn_move_right)
        center_layout.addLayout(move_btns_layout)

        columns_layout.addLayout(center_layout, 1)

        # Right column: to add
        right_layout = QVBoxLayout()
        self.add_list = QListWidget()
        self.add_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        right_layout.addWidget(self.add_list)

        btn_cancel_add = QPushButton("← Cancel")
        btn_cancel_add.setToolTip("Remove from add list")
        btn_cancel_add.clicked.connect(self._cancel_add)
        right_layout.addWidget(btn_cancel_add)

        columns_layout.addLayout(right_layout, 1)

        layout.addLayout(columns_layout)

        # Bulk actions
        bulk_layout = QHBoxLayout()
        btn_all_remove = QPushButton("All → Remove")
        btn_all_remove.setToolTip("Move all current values to remove list")
        btn_all_remove.clicked.connect(self._move_all_to_remove)
        bulk_layout.addWidget(btn_all_remove)

        bulk_layout.addStretch()

        btn_all_add = QPushButton("All → Add")
        btn_all_add.setToolTip("Move all current values to add list")
        btn_all_add.clicked.connect(self._move_all_to_add)
        bulk_layout.addWidget(btn_all_add)
        layout.addLayout(bulk_layout)

        # New value input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("New value:"))

        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText(f"Enter new {self.ptype} value...")
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

    def _populate_current_list(self):
        """Populate the current values list with counts."""
        self.current_list.clear()
        for value in self._current:
            count = self._value_counts.get(value, 0)
            display = f"{value} ({count})"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, value)
            self.current_list.addItem(item)

    def _move_to_remove(self):
        """Move selected items from current to remove list."""
        selected = self.current_list.selectedItems()
        for item in selected:
            value = item.data(Qt.ItemDataRole.UserRole)
            if value in self._current:
                self._current.remove(value)
                self._to_remove.append(value)

        self._populate_current_list()
        self._populate_remove_list()

    def _move_to_add(self):
        """Move selected items from current to add list."""
        selected = self.current_list.selectedItems()
        for item in selected:
            value = item.data(Qt.ItemDataRole.UserRole)
            if value in self._current:
                self._current.remove(value)
                self._to_add.append(value)

        self._populate_current_list()
        self._populate_add_list()

    def _restore_from_remove(self):
        """Move selected items from remove back to current."""
        selected = self.remove_list.selectedItems()
        for item in selected:
            value = item.data(Qt.ItemDataRole.UserRole)
            if value in self._to_remove:
                self._to_remove.remove(value)
                self._current.append(value)

        self._populate_current_list()
        self._populate_remove_list()

    def _cancel_add(self):
        """Remove selected items from add list."""
        selected = self.add_list.selectedItems()
        for item in selected:
            value = item.data(Qt.ItemDataRole.UserRole)
            if value in self._to_add:
                self._to_add.remove(value)
                # If it was originally a current value, restore it
                if value in self._value_counts:
                    self._current.append(value)

        self._populate_current_list()
        self._populate_add_list()

    def _move_all_to_remove(self):
        """Move all current values to remove list."""
        for value in self._current:
            self._to_remove.append(value)
        self._current.clear()
        self._populate_current_list()
        self._populate_remove_list()

    def _move_all_to_add(self):
        """Move all current values to add list."""
        for value in self._current:
            self._to_add.append(value)
        self._current.clear()
        self._populate_current_list()
        self._populate_add_list()

    def _populate_remove_list(self):
        """Populate the remove list."""
        self.remove_list.clear()
        for value in self._to_remove:
            count = self._value_counts.get(value, 0)
            display = f"{value} ({count})"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, value)
            self.remove_list.addItem(item)

    def _populate_add_list(self):
        """Populate the add list."""
        self.add_list.clear()
        for value in self._to_add:
            count = self._value_counts.get(value, 0)
            if count > 0:
                display = f"{value} ({count})"
            else:
                display = f"{value} (new)"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, value)
            self.add_list.addItem(item)

    def _add_new_value(self):
        """Add a new value to the add list."""
        text = self.value_input.text().strip()
        if not text:
            return

        # Convert to the appropriate type
        try:
            if self.ptype == "int":
                value = int(text)
            elif self.ptype == "float":
                value = float(text)
            elif self.ptype == "bool":
                value = text.lower() in ("true", "1", "yes", "oui")
            else:
                value = text

            # Don't add duplicates
            if value in self._to_add or value in self._current:
                self.value_input.clear()
                return

            self._to_add.append(value)
            self._populate_add_list()
            self.value_input.clear()

        except ValueError:
            pass  # Invalid input

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
        prop_type: dict,
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
