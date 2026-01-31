"""
Dialog for managing property values across all videos.
"""

from collections import Counter

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class PropertyValuesDialog(QDialog):
    """
    Dialog for viewing and managing all values of a property.

    Features:
    - List all values with their usage count
    - Delete values (removes from all videos)
    - Rename/merge values
    - Apply modifiers (lowercase, uppercase)
    """

    def __init__(self, prop_name: str, prop_type: dict, database, parent=None):
        super().__init__(parent)
        self.prop_name = prop_name
        self.prop_type = prop_type
        self.database = database
        self._values_count: dict[str, int] = {}
        self._modified = False

        self.setWindowTitle(f"Values - {prop_name}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        # Header info
        type_name = self.prop_type.get("type", "str")  # Already a string
        multiple = "Yes" if self.prop_type.get("multiple") else "No"
        info_label = QLabel(
            f"<b>{self.prop_name}</b> (type: {type_name}, multiple: {multiple})"
        )
        layout.addWidget(info_label)

        # Main content: values list and actions
        content_layout = QHBoxLayout()

        # Values list
        list_layout = QVBoxLayout()
        list_layout.addWidget(
            QLabel("Values (click to select, right-click for actions):")
        )

        self.values_list = QListWidget()
        self.values_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.values_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.values_list.customContextMenuRequested.connect(self._on_context_menu)
        list_layout.addWidget(self.values_list)

        content_layout.addLayout(list_layout, 1)

        # Actions panel
        actions_layout = QVBoxLayout()
        actions_layout.addWidget(QLabel("Actions:"))

        self.btn_delete = QPushButton("Delete Selected")
        self.btn_delete.setToolTip("Remove selected values from all videos")
        self.btn_delete.clicked.connect(self._on_delete)
        actions_layout.addWidget(self.btn_delete)

        self.btn_rename = QPushButton("Rename Value...")
        self.btn_rename.setToolTip("Rename a value (merges if target exists)")
        self.btn_rename.clicked.connect(self._on_rename)
        actions_layout.addWidget(self.btn_rename)

        actions_layout.addSpacing(20)
        actions_layout.addWidget(QLabel("Apply to all values:"))

        # Get available modifiers from PropertyValueModifier
        from pysaurus.database.property_value_modifier import PropertyValueModifier

        modifiers = PropertyValueModifier.get_modifiers()
        for mod_name in modifiers:
            btn = QPushButton(mod_name.replace("_", " ").title())
            btn.setToolTip(f"Apply '{mod_name}' to all values")
            btn.clicked.connect(lambda _, m=mod_name: self._on_apply_modifier(m))
            actions_layout.addWidget(btn)

        actions_layout.addStretch()

        # Stats
        self.stats_label = QLabel("")
        actions_layout.addWidget(self.stats_label)

        content_layout.addLayout(actions_layout)
        layout.addLayout(content_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)

    def _load_values(self):
        """Load all values for this property."""
        self.values_list.clear()
        self._values_count.clear()

        if not self.database:
            return

        # Get all values with counts
        all_values = self.database.videos_tag_get(self.prop_name)
        counter = Counter()
        for values in all_values.values():
            counter.update(values)

        self._values_count = dict(counter)

        # Sort by count (descending) then by value
        sorted_values = sorted(
            self._values_count.items(), key=lambda x: (-x[1], str(x[0]).lower())
        )

        for value, count in sorted_values:
            item = QListWidgetItem(f"{value} ({count})")
            item.setData(Qt.ItemDataRole.UserRole, value)
            self.values_list.addItem(item)

        # Update stats
        total_values = len(self._values_count)
        total_usages = sum(self._values_count.values())
        self.stats_label.setText(
            f"{total_values} unique values\n{total_usages} total usages"
        )

    def _get_selected_values(self) -> list:
        """Get the selected values."""
        return [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.values_list.selectedItems()
        ]

    def _on_context_menu(self, pos):
        """Show context menu for values."""
        item = self.values_list.itemAt(pos)
        if not item:
            return

        value = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)

        menu.addAction("Delete", lambda: self._delete_values([value]))
        menu.addAction("Rename...", lambda: self._rename_value(value))
        menu.addSeparator()
        menu.addAction("Copy Value", lambda: self._copy_value(value))

        menu.exec(self.values_list.mapToGlobal(pos))

    def _on_delete(self):
        """Delete selected values."""
        values = self._get_selected_values()
        if not values:
            QMessageBox.information(
                self, "No Selection", "Please select values to delete."
            )
            return

        self._delete_values(values)

    def _delete_values(self, values: list):
        """Delete the given values from all videos."""
        count = len(values)
        reply = QMessageBox.question(
            self,
            "Delete Values",
            f"Delete {count} value(s) from all videos?\n\n"
            "This will remove these values from every video that has them.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.database.algos.delete_property_values(self.prop_name, values)
                self._modified = True
                self._load_values()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete values: {e}")

    def _on_rename(self):
        """Rename a selected value."""
        values = self._get_selected_values()
        if len(values) != 1:
            QMessageBox.information(
                self, "Select One", "Please select exactly one value to rename."
            )
            return

        self._rename_value(values[0])

    def _rename_value(self, old_value):
        """Rename a value (merges if target exists)."""
        new_value, ok = QInputDialog.getText(
            self, "Rename Value", f"Rename '{old_value}' to:", text=str(old_value)
        )

        if not ok or not new_value.strip():
            return

        new_value = new_value.strip()
        if new_value == str(old_value):
            return

        # Check if merging
        if new_value in self._values_count:
            reply = QMessageBox.question(
                self,
                "Merge Values",
                f"'{new_value}' already exists. Merge '{old_value}' into it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            self.database.algos.replace_property_values(
                self.prop_name, [old_value], new_value
            )
            self._modified = True
            self._load_values()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to rename value: {e}")

    def _on_apply_modifier(self, modifier: str):
        """Apply a modifier to all property values."""
        reply = QMessageBox.question(
            self,
            f"Apply {modifier.title()}",
            f"Apply '{modifier}' to ALL values of '{self.prop_name}'?\n\n"
            "This will modify values across all videos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.database.ops.apply_on_prop_value(self.prop_name, modifier)
                self._modified = True
                self._load_values()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to apply modifier: {e}")

    def _copy_value(self, value):
        """Copy value to clipboard."""
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(str(value))

    def was_modified(self) -> bool:
        """Return whether any changes were made."""
        return self._modified
