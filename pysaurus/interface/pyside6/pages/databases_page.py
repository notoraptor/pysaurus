"""
Databases page for selecting and creating databases.
"""

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.constants import VIDEO_SUPPORTED_EXTENSIONS
from pysaurus.interface.pyside6.app_context import AppContext


class DatabaseItemWidget(QFrame):
    """Widget for a single database with expandable action buttons."""

    open_clicked = Signal(str, bool)  # (name, update)
    delete_clicked = Signal(str)  # name
    expanded = Signal(object)  # self - emitted when this widget expands

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.name = name
        self._expanded = False
        self._setup_ui()

    def _setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Database name label (centered)
        self.name_label = QLabel(self.name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.name_label)

        # Action buttons container (initially hidden)
        self.buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(self.buttons_widget)
        buttons_layout.setContentsMargins(0, 4, 0, 0)
        buttons_layout.setSpacing(8)

        buttons_layout.addStretch()

        self.btn_open = QPushButton("Open")
        self.btn_open.setToolTip("Open database")
        self.btn_open.clicked.connect(lambda: self.open_clicked.emit(self.name, False))
        buttons_layout.addWidget(self.btn_open)

        self.btn_update = QPushButton("Update")
        self.btn_update.setToolTip("Open and update database")
        self.btn_update.clicked.connect(lambda: self.open_clicked.emit(self.name, True))
        buttons_layout.addWidget(self.btn_update)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setToolTip("Delete database")
        self.btn_delete.setStyleSheet(
            "QPushButton { background-color: #cc3333; color: white; font-weight: bold; }"
            "QPushButton:hover { background-color: #dd4444; }"
        )
        self.btn_delete.clicked.connect(lambda: self.delete_clicked.emit(self.name))
        buttons_layout.addWidget(self.btn_delete)

        buttons_layout.addStretch()

        self.buttons_widget.setVisible(False)
        layout.addWidget(self.buttons_widget)

        self._update_style()

    def _update_style(self):
        if self._expanded:
            self.setStyleSheet("""
                DatabaseItemWidget {
                    background-color: #e3f2fd;
                    border: 1px solid #1976d2;
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                DatabaseItemWidget {
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                DatabaseItemWidget:hover {
                    background-color: #e8e8e8;
                    border-color: #bbb;
                }
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_expanded()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Double-click opens directly
            self.open_clicked.emit(self.name, False)
        super().mouseDoubleClickEvent(event)

    def toggle_expanded(self):
        self._expanded = not self._expanded
        self.buttons_widget.setVisible(self._expanded)
        self._update_style()
        if self._expanded:
            self.expanded.emit(self)

    def collapse(self):
        self._expanded = False
        self.buttons_widget.setVisible(False)
        self._update_style()


class DatabasesPage(QWidget):
    """
    Page for selecting and creating databases.

    Layout:
    - Left: list of existing databases with action buttons
    - Right: form to create a new database
    """

    # Signals
    database_opening = Signal(str, bool)  # (name, update)
    database_creating = Signal(str, list, bool)  # (name, folders, update)

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._setup_ui()
        self._refresh_database_list()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QHBoxLayout(self)

        # Left side: existing databases
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        title_label = QLabel("Existing Databases")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSizeF(title_font.pointSizeF() * 1.6)
        title_label.setFont(title_font)
        left_layout.addWidget(title_label)

        # Scroll area for database items
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.db_container = QWidget()
        self.db_layout = QVBoxLayout(self.db_container)
        self.db_layout.setSpacing(4)
        self.db_layout.setContentsMargins(4, 4, 4, 4)
        self.db_layout.addStretch()

        scroll_area.setWidget(self.db_container)
        left_layout.addWidget(scroll_area)

        self._db_widgets: list[DatabaseItemWidget] = []

        layout.addWidget(left_widget)

        # Right side: create new database
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        create_title = QLabel("Create New Database")
        create_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        create_font = create_title.font()
        create_font.setBold(True)
        create_font.setPointSizeF(create_font.pointSizeF() * 1.6)
        create_title.setFont(create_font)
        right_layout.addWidget(create_title)

        # Name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter database name")
        name_layout.addWidget(self.name_input)
        right_layout.addLayout(name_layout)

        # Sources list
        right_layout.addWidget(QLabel("Sources (folders and files):"))
        self.sources_list = QListWidget()
        right_layout.addWidget(self.sources_list)

        # Add source buttons
        source_btn_layout = QHBoxLayout()
        self.btn_add_folder = QPushButton("Add Folder")
        self.btn_add_folder.clicked.connect(self._on_add_folder)
        source_btn_layout.addWidget(self.btn_add_folder)

        self.btn_add_file = QPushButton("Add File")
        self.btn_add_file.clicked.connect(self._on_add_file)
        source_btn_layout.addWidget(self.btn_add_file)

        self.btn_remove_source = QPushButton("Remove")
        self.btn_remove_source.clicked.connect(self._on_remove_source)
        source_btn_layout.addWidget(self.btn_remove_source)

        right_layout.addLayout(source_btn_layout)

        # Create button
        self.btn_create = QPushButton("Create Database")
        self.btn_create.clicked.connect(self._on_create_clicked)
        right_layout.addWidget(self.btn_create)

        layout.addWidget(right_widget)

    def refresh(self):
        """Refresh the page (public interface)."""
        self._refresh_database_list()

    def _refresh_database_list(self):
        """Refresh the list of databases."""
        # Clear existing widgets
        for widget in self._db_widgets:
            self.db_layout.removeWidget(widget)
            widget.deleteLater()
        self._db_widgets.clear()

        # Add new widgets
        for name in self.ctx.get_database_names():
            widget = DatabaseItemWidget(name)
            widget.open_clicked.connect(self._on_db_open)
            widget.delete_clicked.connect(self._on_db_delete)
            widget.expanded.connect(self._on_db_expanded)
            # Insert before the stretch
            self.db_layout.insertWidget(len(self._db_widgets), widget)
            self._db_widgets.append(widget)

    def _collapse_all_except(self, except_widget: DatabaseItemWidget | None = None):
        """Collapse all database widgets except the specified one."""
        for widget in self._db_widgets:
            if widget is not except_widget:
                widget.collapse()

    def _on_db_expanded(self, widget: DatabaseItemWidget):
        """Handle database widget expansion - collapse others."""
        self._collapse_all_except(widget)

    def _on_db_open(self, name: str, update: bool):
        """Handle open/update request from a database widget."""
        self.database_opening.emit(name, update)

    def _on_db_delete(self, name: str):
        """Handle delete request from a database widget."""
        reply = QMessageBox.question(
            self,
            "Delete Database",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.ctx.application.delete_database_from_name(name)
            self._refresh_database_list()

    def _normalize_path(self, path: str) -> str:
        """Normalize a path to absolute with system separators."""
        return os.path.normpath(os.path.abspath(path))

    def _get_existing_paths(self) -> set[str]:
        """Get set of normalized paths already in the sources list."""
        paths = set()
        for i in range(self.sources_list.count()):
            text = self.sources_list.item(i).text()
            # Remove emoji prefix
            if text.startswith("📁 ") or text.startswith("📄 "):
                paths.add(self._normalize_path(text[2:].strip()))
            else:
                paths.add(self._normalize_path(text))
        return paths

    def _on_add_folder(self):
        """Add a folder to sources."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            folder = self._normalize_path(folder)
            if folder in self._get_existing_paths():
                QMessageBox.information(
                    self,
                    "Already in List",
                    f"This folder is already in the list:\n{folder}",
                )
            else:
                self.sources_list.addItem(f"📁 {folder}")

    def _on_add_file(self):
        """Add files to sources."""
        ext_filter = " ".join(f"*.{ext}" for ext in sorted(VIDEO_SUPPORTED_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Video Files",
            "",
            f"Video files ({ext_filter});;All files (*)",
        )
        existing = self._get_existing_paths()
        added = 0
        for f in files:
            f = self._normalize_path(f)
            if f not in existing:
                self.sources_list.addItem(f"📄 {f}")
                existing.add(f)
                added += 1
        if files and added < len(files):
            skipped = len(files) - added
            QMessageBox.information(
                self,
                "Some Files Already in List",
                f"{skipped} file(s) were already in the list.",
            )

    def _on_remove_source(self):
        """Remove selected source."""
        item = self.sources_list.currentItem()
        if item:
            self.sources_list.takeItem(self.sources_list.row(item))

    def _on_create_clicked(self):
        """Handle create button click."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a database name.")
            return

        sources = []
        for i in range(self.sources_list.count()):
            text = self.sources_list.item(i).text()
            # Remove the emoji prefix
            if text.startswith("📁 ") or text.startswith("📄 "):
                sources.append(text[2:].strip())
            else:
                sources.append(text)

        if not sources:
            QMessageBox.warning(self, "Error", "Please add at least one source.")
            return

        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Create Database",
            f"Create database '{name}' with {len(sources)} source(s)?\n\n"
            "This will scan all sources for video files.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Emit signal and let main window handle the navigation
        self.database_creating.emit(name, sources, True)

        # Clear form
        self.name_input.clear()
        self.sources_list.clear()
