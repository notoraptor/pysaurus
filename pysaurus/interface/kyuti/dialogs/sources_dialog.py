"""
Dialog for selecting video sources (filters).

Two tabs:
- Simple: checkbox-based flag selection (existing behavior)
- Advanced: free-text searchexp expression, with the database's saved searches
"""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pysaurus.application.exceptions import PysaurusError
from pysaurus.core.language import say
from pysaurus.database.saved_search import SavedSearch
from pysaurus.interface.kyuti.utils.text import elide, saved_search_tooltip

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
    The advanced tab allows entering a searchexp expression. Given `ctx`
    (the AppContext facade), it also lists the database's saved searches;
    the combo mirrors the editor, so Delete acts on the expression shown.
    """

    def __init__(
        self,
        current_sources: list[list[str]] | None = None,
        current_expression: str | None = None,
        parent=None,
        start_tab: int = 0,
        ctx=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(say("Select Sources"))
        self.setMinimumWidth(450)

        self._checkboxes: dict[str, QCheckBox] = {}
        self._current_sources = current_sources or []
        self._current_expression = current_expression
        self._ctx = ctx
        self._saved_searches: list[SavedSearch] = []
        self._synced_index = 0
        self._error_expression: str | None = None

        self._setup_ui(start_tab)
        self._load_current_sources()
        if start_tab == 1:
            self._expression_edit.setFocus()

    def _setup_ui(self, start_tab: int):
        """Set up the UI with tabs."""
        layout = QVBoxLayout(self)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.addTab(self._create_simple_tab(), say("Simple"))
        self._tabs.addTab(self._create_advanced_tab(), say("Advanced"))
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
        layout.addWidget(QLabel(say("Select which videos to display:")))

        # Readable group
        readable_group = QGroupBox(say("Readable"))
        readable_layout = QVBoxLayout(readable_group)

        # Found subgroup
        found_group = QGroupBox(say("Found"))
        found_layout = QVBoxLayout(found_group)
        self._add_checkbox(
            found_layout, "readable.found.with_thumbnails", say("With thumbnails")
        )
        self._add_checkbox(
            found_layout, "readable.found.without_thumbnails", say("Without thumbnails")
        )
        readable_layout.addWidget(found_group)

        # Not found subgroup
        not_found_group = QGroupBox(say("Not Found"))
        not_found_layout = QVBoxLayout(not_found_group)
        self._add_checkbox(
            not_found_layout,
            "readable.not_found.with_thumbnails",
            say("With thumbnails"),
        )
        self._add_checkbox(
            not_found_layout,
            "readable.not_found.without_thumbnails",
            say("Without thumbnails"),
        )
        readable_layout.addWidget(not_found_group)

        layout.addWidget(readable_group)

        # Unreadable group
        unreadable_group = QGroupBox(say("Unreadable"))
        unreadable_layout = QVBoxLayout(unreadable_group)
        self._add_checkbox(unreadable_layout, "unreadable.found", say("Found"))
        self._add_checkbox(unreadable_layout, "unreadable.not_found", say("Not Found"))
        layout.addWidget(unreadable_group)

        # Quick select buttons
        btn_layout = QHBoxLayout()
        btn_all = QPushButton(say("Select All"))
        btn_all.clicked.connect(self._select_all)
        btn_layout.addWidget(btn_all)

        btn_none = QPushButton(say("Select None"))
        btn_none.clicked.connect(self._select_none)
        btn_layout.addWidget(btn_none)

        btn_valid = QPushButton(say("Valid Only"))
        btn_valid.clicked.connect(self._select_valid)
        btn_layout.addWidget(btn_valid)

        layout.addLayout(btn_layout)
        return widget

    def _create_advanced_tab(self) -> QWidget:
        """Create the advanced expression tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._saved_bar = QWidget()
        saved_layout = QHBoxLayout(self._saved_bar)
        saved_layout.setContentsMargins(0, 0, 0, 0)
        saved_layout.addWidget(QLabel(say("Saved searches:")))
        self._saved_combo = QComboBox()
        self._saved_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._saved_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self._saved_combo.activated.connect(self._on_saved_search_activated)
        saved_layout.addWidget(self._saved_combo, 1)
        self._save_button = QPushButton(say("Save..."))
        self._save_button.clicked.connect(self._on_save_search)
        saved_layout.addWidget(self._save_button)
        self._rename_button = QPushButton(say("Rename..."))
        self._rename_button.clicked.connect(self._on_rename_search)
        saved_layout.addWidget(self._rename_button)
        self._delete_button = QPushButton(say("Delete"))
        self._delete_button.clicked.connect(self._on_delete_search)
        saved_layout.addWidget(self._delete_button)
        self._saved_bar.setVisible(self._ctx is not None)
        layout.addWidget(self._saved_bar)

        layout.addWidget(QLabel(say("Enter a search expression to filter videos:")))

        self._expression_edit = QTextEdit()
        self._expression_edit.setPlaceholderText(
            say('e.g. width > 1080 and found and "eng" in audio_languages')
        )
        self._expression_edit.setAcceptRichText(False)
        self._expression_edit.installEventFilter(self)
        if self._current_expression:
            self._expression_edit.setPlainText(self._current_expression)
        self._expression_edit.textChanged.connect(self._sync_saved_search)
        layout.addWidget(self._expression_edit)

        self._expression_error = QLabel()
        self._expression_error.setStyleSheet("color: red;")
        self._expression_error.setWordWrap(True)
        self._expression_error.hide()
        layout.addWidget(self._expression_error)

        self._reload_saved_searches()
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

    def _reload_saved_searches(self):
        self._saved_searches = self._ctx.get_saved_searches() if self._ctx else []
        self._saved_combo.clear()
        none_label = say("(select a saved search)")
        self._saved_combo.addItem(none_label, None)
        self._saved_combo.setItemData(0, none_label, Qt.ItemDataRole.ToolTipRole)
        for search in self._saved_searches:
            self._saved_combo.addItem(elide(search.label), search.expression)
            self._saved_combo.setItemData(
                self._saved_combo.count() - 1,
                saved_search_tooltip(search),
                Qt.ItemDataRole.ToolTipRole,
            )
        self._sync_saved_search()

    def _sync_saved_search(self):
        """Derive combo, buttons and error from the editor text.

        Save shows while the text is not a saved search, Rename instead.
        """
        text = self.get_expression()
        if text != self._error_expression:
            self._clear_expression_error()
        index = self._saved_combo.findData(text) if text else -1
        saved = index > 0
        self._synced_index = max(index, 0)
        self._saved_combo.setCurrentIndex(self._synced_index)
        self._saved_combo.setToolTip(
            self._saved_combo.itemData(self._synced_index, Qt.ItemDataRole.ToolTipRole)
        )
        self._save_button.setVisible(not saved)
        self._save_button.setEnabled(bool(text) and not saved)
        self._rename_button.setVisible(saved)
        self._rename_button.setEnabled(saved)
        self._delete_button.setEnabled(saved)

    def _on_saved_search_activated(self, index: int):
        """Load the chosen search, or clear the editor for the none entry."""
        if index == self._synced_index:
            return
        self._expression_edit.setPlainText(self._saved_combo.itemData(index) or "")
        self._expression_edit.setFocus()

    def _on_save_search(self):
        expression = self.get_expression()
        if expression:
            self._ask_name_and_save(say("Save search"), expression, "")

    def _on_rename_search(self):
        expression = self._saved_combo.currentData()
        if expression:
            names = {s.expression: s.name for s in self._saved_searches}
            self._ask_name_and_save(
                say("Rename search"), expression, names.get(expression) or ""
            )

    def _ask_name_and_save(self, title: str, expression: str, current_name: str):
        name, ok = QInputDialog.getText(
            self, title, say("Name (optional):"), text=current_name
        )
        if not ok:
            return
        try:
            self._ctx.save_search(expression, name)
        except PysaurusError as exc:
            self._show_expression_error(str(exc))
            return
        self._clear_expression_error()
        self._reload_saved_searches()

    def _on_delete_search(self):
        expression = self._saved_combo.currentData()
        if expression:
            self._ctx.delete_saved_search(expression)
            self._reload_saved_searches()

    def _show_expression_error(self, message: str):
        self._error_expression = self.get_expression()
        self._expression_error.setText(message)
        self._expression_error.show()

    def _clear_expression_error(self):
        self._error_expression = None
        self._expression_error.hide()

    def eventFilter(self, obj, event):
        if obj is self._expression_edit and event.type() == QEvent.Type.KeyPress:
            if (
                event.modifiers() == Qt.KeyboardModifier.ShiftModifier
                and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            ):
                self.accept()
                return True
            if event.modifiers() == Qt.KeyboardModifier.NoModifier and event.key() in (
                Qt.Key.Key_Up,
                Qt.Key.Key_Down,
            ):
                cursor = self._expression_edit.textCursor()
                pos_before = cursor.position()
                if event.key() == Qt.Key.Key_Up:
                    cursor.movePosition(QTextCursor.MoveOperation.Up)
                    if cursor.position() == pos_before:
                        cursor.movePosition(QTextCursor.MoveOperation.Start)
                else:
                    cursor.movePosition(QTextCursor.MoveOperation.Down)
                    if cursor.position() == pos_before:
                        cursor.movePosition(QTextCursor.MoveOperation.End)
                self._expression_edit.setTextCursor(cursor)
                return True
        return super().eventFilter(obj, event)

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
