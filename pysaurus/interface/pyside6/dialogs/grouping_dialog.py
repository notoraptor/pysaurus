"""
Dialog for setting video grouping.
"""

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QRadioButton,
    QVBoxLayout,
)

from pysaurus.interface.common.common import FIELD_MAP


class GroupingDialog(QDialog):
    """
    Dialog for setting how videos are grouped.

    Options:
    - Field to group by (video attribute or custom property)
    - Sort order (by field value, by count, or by length)
    - Reverse order
    - Allow singletons (groups with only one video)
    """

    def __init__(
        self, prop_types: list = None, current_grouping: dict | None = None, parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle("Set Grouping")
        self.setMinimumWidth(350)

        self._prop_types = prop_types or []
        self._current = current_grouping or {}

        self._setup_ui()
        self._load_current()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        # Field selection
        field_group = QGroupBox("Group By")
        field_layout = QFormLayout(field_group)

        # Field type (attribute or property)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Video Attribute", "Custom Property"])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        field_layout.addRow("Type:", self.type_combo)

        # Field selector
        self.field_combo = QComboBox()
        field_layout.addRow("Field:", self.field_combo)

        layout.addWidget(field_group)

        # Sort options
        sort_group = QGroupBox("Sort Groups")
        sort_layout = QVBoxLayout(sort_group)

        self.sort_button_group = QButtonGroup(self)
        self.sort_field = QRadioButton("By field value")
        self.sort_count = QRadioButton("By video count")
        self.sort_length = QRadioButton("By total length")

        self.sort_button_group.addButton(self.sort_field, 0)
        self.sort_button_group.addButton(self.sort_count, 1)
        self.sort_button_group.addButton(self.sort_length, 2)

        sort_layout.addWidget(self.sort_field)
        sort_layout.addWidget(self.sort_count)
        sort_layout.addWidget(self.sort_length)

        layout.addWidget(sort_group)

        # Options
        options_layout = QHBoxLayout()

        self.reverse_check = QCheckBox("Reverse order")
        options_layout.addWidget(self.reverse_check)

        self.singletons_check = QCheckBox("Allow singletons")
        self.singletons_check.setToolTip("Show groups with only one video")
        options_layout.addWidget(self.singletons_check)

        layout.addLayout(options_layout)

        # Dialog buttons
        button_box = QDialogButtonBox()
        button_box.addButton("Apply", QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton("Clear Grouping", QDialogButtonBox.ButtonRole.ResetRole)
        button_box.addButton(QDialogButtonBox.StandardButton.Cancel)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.clicked.connect(self._on_button_clicked)

        layout.addWidget(button_box)

        # Initialize field combo
        self._populate_fields()

    def _populate_fields(self):
        """Populate the field combo based on type selection."""
        self.field_combo.clear()

        if self.type_combo.currentIndex() == 0:
            # Video attributes
            for field_info in FIELD_MAP.allowed:
                self.field_combo.addItem(field_info.title, field_info.name)
        else:
            # Custom properties
            for prop_type in self._prop_types:
                self.field_combo.addItem(prop_type["name"], prop_type["name"])

    def _on_type_changed(self, index: int):
        """Handle field type change."""
        self._populate_fields()

    def _on_button_clicked(self, button):
        """Handle button clicks."""
        role = self.sender().buttonRole(button)
        if role == QDialogButtonBox.ButtonRole.ResetRole:
            self._clear_result = True
            self.accept()

    def _load_current(self):
        """Load current grouping settings."""
        self._clear_result = False

        if not self._current:
            self.sort_field.setChecked(True)
            return

        # Set type and field
        is_property = self._current.get("is_property", False)
        self.type_combo.setCurrentIndex(1 if is_property else 0)
        self._populate_fields()

        field = self._current.get("field", "")
        index = self.field_combo.findData(field)
        if index >= 0:
            self.field_combo.setCurrentIndex(index)

        # Set sorting
        sorting = self._current.get("sorting", "field")
        if sorting == "field":
            self.sort_field.setChecked(True)
        elif sorting == "count":
            self.sort_count.setChecked(True)
        elif sorting == "length":
            self.sort_length.setChecked(True)

        # Set options
        self.reverse_check.setChecked(self._current.get("reverse", False))
        self.singletons_check.setChecked(self._current.get("allow_singletons", False))

    def get_grouping(self) -> dict | None:
        """Get the grouping settings."""
        if self._clear_result:
            return None

        # Get sorting
        if self.sort_field.isChecked():
            sorting = "field"
        elif self.sort_count.isChecked():
            sorting = "count"
        else:
            sorting = "length"

        return {
            "field": self.field_combo.currentData(),
            "is_property": self.type_combo.currentIndex() == 1,
            "sorting": sorting,
            "reverse": self.reverse_check.isChecked(),
            "allow_singletons": self.singletons_check.isChecked(),
        }
