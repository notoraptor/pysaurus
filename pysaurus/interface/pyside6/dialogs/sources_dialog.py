"""
Dialog for selecting video sources (filters).

Two tabs:
- Simple: checkbox-based flag selection (existing behavior)
- Advanced: free-text searchexp expression
"""

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
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

    The simple tab has the checkbox-based source tree.
    The advanced tab allows entering a searchexp expression.
    """

    def __init__(
        self,
        current_sources: list[list[str]] | None = None,
        current_expression: str | None = None,
        parent=None,
        start_tab: int = 0,
    ):
        super().__init__(parent)
        self.setWindowTitle("Select Sources")
        self.setMinimumWidth(450)

        self._checkboxes: dict[str, QCheckBox] = {}
        self._current_sources = current_sources or []
        self._current_expression = current_expression

        self._setup_ui(start_tab)
        self._load_current_sources()
        if start_tab == 1:
            self._expression_edit.setFocus()

    def _setup_ui(self, start_tab: int):
        """Set up the UI with tabs."""
        layout = QVBoxLayout(self)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.addTab(self._create_simple_tab(), "Simple")
        self._tabs.addTab(self._create_advanced_tab(), "Advanced")
        self._tabs.setCurrentIndex(start_tab)
        layout.addWidget(self._tabs)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_simple_tab(self) -> QWidget:
        """Create the simple checkbox-based tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

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
        return widget

    def _create_advanced_tab(self) -> QWidget:
        """Create the advanced expression tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Enter a search expression to filter videos:"))

        self._expression_edit = QTextEdit()
        self._expression_edit.setPlaceholderText(
            'e.g. width > 1080 and found and "eng" in audio_languages'
        )
        self._expression_edit.setAcceptRichText(False)
        if self._current_expression:
            self._expression_edit.setPlainText(self._current_expression)
        layout.addWidget(self._expression_edit)

        self._expression_error = QLabel()
        self._expression_error.setStyleSheet("color: red;")
        self._expression_error.setWordWrap(True)
        self._expression_error.hide()
        layout.addWidget(self._expression_error)

        return widget

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
        for source_path in self._current_sources:
            prefix = ".".join(source_path)
            if prefix in self._checkboxes:
                self._checkboxes[prefix].setChecked(True)
            else:
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

    def is_advanced(self) -> bool:
        """Return True if the advanced tab is selected."""
        return self._tabs.currentIndex() == 1

    def get_sources(self) -> list[list[str]]:
        """Get the selected sources as a list of paths."""
        sources = []
        for key, cb in self._checkboxes.items():
            if cb.isChecked():
                sources.append(key.split("."))
        return sources

    def get_expression(self) -> str | None:
        """Get the expression text, or None if empty."""
        text = self._expression_edit.toPlainText().strip()
        return text or None
