"""
Dialog for filling a property with terms extracted from video titles.
"""

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)


class FillPropertyDialog(QDialog):
    """
    Dialog to fill a string-multiple property with terms from video titles.

    The terms are extracted from video filenames using the database's
    videos_get_terms() method.
    """

    def __init__(self, prop_types: list, parent=None):
        super().__init__(parent)
        self.prop_types = prop_types
        self._selected_prop = None
        self._only_empty = False

        # Filter to only string-multiple properties
        self._eligible_props = [
            pt for pt in prop_types if pt.get("type") == "str" and pt.get("multiple")
        ]

        self.setWindowTitle("Fill Property with Terms")
        self.setMinimumWidth(400)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        # Description
        desc_label = QLabel(
            "Extract terms from video filenames and add them to a property.\n"
            "This is useful for automatically tagging videos based on their names."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(desc_label)

        # Form
        form_layout = QFormLayout()

        # Property selector
        self.prop_combo = QComboBox()
        if self._eligible_props:
            for pt in self._eligible_props:
                self.prop_combo.addItem(pt["name"], pt)
        else:
            self.prop_combo.addItem("(No eligible properties)")
            self.prop_combo.setEnabled(False)
        form_layout.addRow("Property:", self.prop_combo)

        # Only empty checkbox
        self.only_empty_check = QCheckBox("Only fill videos without values")
        self.only_empty_check.setToolTip(
            "If checked, only videos that don't have any values for this property "
            "will be filled. Existing values will not be modified."
        )
        form_layout.addRow("", self.only_empty_check)

        layout.addLayout(form_layout)

        # Info about eligible properties
        if not self._eligible_props:
            info_label = QLabel(
                "<i>No eligible properties found. "
                "This feature requires a string property with 'multiple' enabled.</i>"
            )
            info_label.setStyleSheet("color: #c00;")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

        layout.addStretch()

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)

        if not self._eligible_props:
            button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        layout.addWidget(button_box)

    def _on_accept(self):
        """Validate and accept."""
        if self._eligible_props:
            self._selected_prop = self.prop_combo.currentData()
            self._only_empty = self.only_empty_check.isChecked()
        self.accept()

    def get_result(self) -> tuple[dict | None, bool]:
        """Return (selected_property, only_empty)."""
        return self._selected_prop, self._only_empty
