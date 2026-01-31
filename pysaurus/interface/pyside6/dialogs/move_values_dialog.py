"""
Dialog for moving property values between properties.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)


class MoveValuesDialog(QDialog):
    """
    Dialog to move values from one property to another.

    Requirements:
    - Source property must be string-multiple
    - Target property must be string type
    """

    def __init__(self, source_prop: dict, prop_types: list, database, parent=None):
        super().__init__(parent)
        self.source_prop = source_prop
        self.prop_types = prop_types
        self.database = database

        self._selected_values: list = []
        self._target_prop: dict | None = None
        self._concatenate = False

        # Filter target properties (string type, different from source)
        self._target_props = [
            pt
            for pt in prop_types
            if pt.get("type") is str and pt["name"] != source_prop["name"]
        ]

        self.setWindowTitle(f"Move Values from {source_prop['name']}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        # Description
        desc_label = QLabel(
            f"Select values from <b>{self.source_prop['name']}</b> to move to another property.\n"
            "The values will be removed from the source and added to the target."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("padding: 5px;")
        layout.addWidget(desc_label)

        # Values list
        layout.addWidget(QLabel("Select values to move:"))
        self.values_list = QListWidget()
        self.values_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.values_list)

        # Target selection
        form_layout = QFormLayout()

        self.target_combo = QComboBox()
        if self._target_props:
            for pt in self._target_props:
                label = (
                    f"{pt['name']} ({'multiple' if pt.get('multiple') else 'single'})"
                )
                self.target_combo.addItem(label, pt)
        else:
            self.target_combo.addItem("(No eligible target properties)")
            self.target_combo.setEnabled(False)
        form_layout.addRow("Move to:", self.target_combo)

        # Concatenate option
        self.concatenate_check = QCheckBox("Concatenate values into one")
        self.concatenate_check.setToolTip(
            "If checked, all selected values will be joined with spaces\n"
            "into a single value in the target property."
        )
        form_layout.addRow("", self.concatenate_check)

        layout.addLayout(form_layout)

        # Warning if no targets
        if not self._target_props:
            warning_label = QLabel(
                "<i>No eligible target properties. "
                "Create another string property first.</i>"
            )
            warning_label.setStyleSheet("color: #c00;")
            layout.addWidget(warning_label)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)

        if not self._target_props:
            button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        layout.addWidget(button_box)

    def _load_values(self):
        """Load all values for the source property."""
        self.values_list.clear()

        if not self.database:
            return

        # Get all values with counts
        from collections import Counter

        all_values = self.database.videos_tag_get(self.source_prop["name"])
        counter = Counter()
        for values in all_values.values():
            counter.update(values)

        # Sort by count (descending)
        sorted_values = sorted(
            counter.items(), key=lambda x: (-x[1], str(x[0]).lower())
        )

        for value, count in sorted_values:
            item = QListWidgetItem(f"{value} ({count})")
            item.setData(Qt.ItemDataRole.UserRole, value)
            self.values_list.addItem(item)

    def _on_accept(self):
        """Validate and accept."""
        self._selected_values = [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.values_list.selectedItems()
        ]

        if not self._selected_values:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "No Selection", "Please select values to move.")
            return

        if self._target_props:
            self._target_prop = self.target_combo.currentData()
            self._concatenate = self.concatenate_check.isChecked()

        self.accept()

    def get_result(self) -> tuple[list, dict | None, bool]:
        """Return (selected_values, target_property, concatenate)."""
        return self._selected_values, self._target_prop, self._concatenate
