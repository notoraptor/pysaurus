"""
Dialog for selecting video sources (filters).
"""

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


# Source tree structure
SOURCE_TREE = {
    "readable": {
        "found": {"with_thumbnails": None, "without_thumbnails": None},
        "not_found": {"with_thumbnails": None, "without_thumbnails": None},
    },
    "unreadable": {"found": None, "not_found": None},
}


class SourcesDialog(QDialog):
    """
    Dialog for selecting video sources.

    The source tree has the structure:
    - readable
      - found
        - with_thumbnails
        - without_thumbnails
      - not_found
        - with_thumbnails
        - without_thumbnails
    - unreadable
      - found
      - not_found
    """

    def __init__(self, current_sources: list[list[str]] | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Sources")
        self.setMinimumWidth(400)

        self._checkboxes: dict[str, QCheckBox] = {}
        self._current_sources = current_sources or []

        self._setup_ui()
        self._load_current_sources()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        # Instructions
        layout.addWidget(QLabel("Select which videos to display:"))

        # Readable group
        readable_group = QGroupBox("Readable")
        readable_layout = QVBoxLayout(readable_group)

        # Found subgroup
        found_group = QGroupBox("Found")
        found_layout = QVBoxLayout(found_group)
        self._add_checkbox(
            found_layout, "readable.found.with_thumbnails", "With thumbnails"
        )
        self._add_checkbox(
            found_layout, "readable.found.without_thumbnails", "Without thumbnails"
        )
        readable_layout.addWidget(found_group)

        # Not found subgroup
        not_found_group = QGroupBox("Not Found")
        not_found_layout = QVBoxLayout(not_found_group)
        self._add_checkbox(
            not_found_layout, "readable.not_found.with_thumbnails", "With thumbnails"
        )
        self._add_checkbox(
            not_found_layout,
            "readable.not_found.without_thumbnails",
            "Without thumbnails",
        )
        readable_layout.addWidget(not_found_group)

        layout.addWidget(readable_group)

        # Unreadable group
        unreadable_group = QGroupBox("Unreadable")
        unreadable_layout = QVBoxLayout(unreadable_group)
        self._add_checkbox(unreadable_layout, "unreadable.found", "Found")
        self._add_checkbox(unreadable_layout, "unreadable.not_found", "Not Found")
        layout.addWidget(unreadable_group)

        # Quick select buttons
        btn_layout = QHBoxLayout()
        btn_all = QPushButton("Select All")
        btn_all.clicked.connect(self._select_all)
        btn_layout.addWidget(btn_all)

        btn_none = QPushButton("Select None")
        btn_none.clicked.connect(self._select_none)
        btn_layout.addWidget(btn_none)

        btn_valid = QPushButton("Valid Only")
        btn_valid.clicked.connect(self._select_valid)
        btn_layout.addWidget(btn_valid)

        layout.addLayout(btn_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _add_checkbox(self, layout: QVBoxLayout, key: str, label: str):
        """Add a checkbox to the layout."""
        cb = QCheckBox(label)
        self._checkboxes[key] = cb
        layout.addWidget(cb)

    def _load_current_sources(self):
        """Load current sources into checkboxes."""
        if not self._current_sources:
            # Default: select valid videos (readable, found, with_thumbnails)
            self._select_valid()
            return

        # Convert source paths to checkbox keys
        # Sources can be partial paths like ["readable"] which should select
        # all checkboxes starting with "readable."
        for source_path in self._current_sources:
            prefix = ".".join(source_path)
            # Check if it's an exact match
            if prefix in self._checkboxes:
                self._checkboxes[prefix].setChecked(True)
            else:
                # It's a partial path - select all checkboxes that start with this prefix
                for key, cb in self._checkboxes.items():
                    if key.startswith(prefix + ".") or key == prefix:
                        cb.setChecked(True)

    def _select_all(self):
        """Select all checkboxes."""
        for cb in self._checkboxes.values():
            cb.setChecked(True)

    def _select_none(self):
        """Deselect all checkboxes."""
        for cb in self._checkboxes.values():
            cb.setChecked(False)

    def _select_valid(self):
        """Select only valid videos (readable, found, with thumbnails)."""
        self._select_none()
        self._checkboxes["readable.found.with_thumbnails"].setChecked(True)

    def get_sources(self) -> list[list[str]]:
        """Get the selected sources as a list of paths."""
        sources = []
        for key, cb in self._checkboxes.items():
            if cb.isChecked():
                sources.append(key.split("."))
        return sources
