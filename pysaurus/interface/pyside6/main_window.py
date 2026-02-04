"""
Main window for PySide6 interface.

Central window with QStackedWidget for page navigation.
"""

from datetime import datetime
from typing import Callable

from PySide6.QtCore import QEvent
from PySide6.QtGui import QAction, QActionGroup, QTextCursor
from PySide6.QtWidgets import (
    QDialog,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPlainTextEdit,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
)

from pysaurus.core.notifications import End
from pysaurus.interface.pyside6.app_context import AppContext
from pysaurus.interface.pyside6.dialogs import EditFoldersDialog, RenameDialog
from pysaurus.interface.pyside6.pages import DatabasesPage, PropertiesPage, VideosPage
from pysaurus.interface.pyside6.pages.process_page import ProcessPage


class SessionLogDialog(QDialog):
    """Dialog to display the session log."""

    def __init__(self, log_entries: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Session Log")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText("\n".join(log_entries))
        # Scroll to the end
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
        layout.addWidget(self.text_edit)


class MainWindow(QMainWindow):
    """
    Main application window.

    Contains:
    - Menu bar (File, View, Help)
    - Central QStackedWidget for page navigation
    - Status bar
    """

    # Page indices (process page is dynamically added/removed)
    PAGE_DATABASES = 0
    PAGE_VIDEOS = 1
    PAGE_PROPERTIES = 2

    def __init__(self):
        super().__init__()
        self.ctx = AppContext()
        self._process_page: ProcessPage | None = None
        self._session_log: list[str] = []
        self._session_start = datetime.now()
        self._log_session_start()
        self._setup_ui()
        self._setup_menu()
        self._connect_signals()
        # Start on databases page (after menu setup)
        self.show_databases_page()

    def _setup_ui(self):
        """Set up the main UI components."""
        self.setWindowTitle("Pysaurus - Video Collection Manager")
        self.resize(1200, 800)

        # Central stacked widget for pages
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Create pages
        self.databases_page = DatabasesPage(self.ctx, self)
        self.videos_page = VideosPage(self.ctx, self)
        self.properties_page = PropertiesPage(self.ctx, self)

        # Add pages to stack
        self.stack.addWidget(self.databases_page)  # Index 0
        self.stack.addWidget(self.videos_page)  # Index 1
        self.stack.addWidget(self.properties_page)  # Index 2

        # Status bar (click to clear message)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        self.status_bar.installEventFilter(self)

    def _setup_menu(self):
        """Set up the menu bar."""
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)

        # File menu
        file_menu = QMenu("&File", self)
        menu_bar.addMenu(file_menu)

        file_menu.addAction("Session &Log...", self._show_session_log)
        file_menu.addSeparator()
        file_menu.addAction("&Quit", self.close)

        # Database menu (only enabled when a database is open)
        self.database_menu = QMenu("D&atabase", self)
        menu_bar.addMenu(self.database_menu)

        self._action_rename_db = self.database_menu.addAction(
            "&Rename Database...", self._on_rename_database
        )
        self._action_edit_folders = self.database_menu.addAction(
            "&Edit Folders...", self._on_edit_folders
        )
        self.database_menu.addSeparator()
        self._action_close_db = self.database_menu.addAction(
            "&Close Database", self._on_close_database
        )

        # View menu
        self.view_menu = QMenu("&View", self)
        menu_bar.addMenu(self.view_menu)

        self._action_view_videos = self.view_menu.addAction(
            "&Videos", self.show_videos_page
        )
        self._action_view_properties = self.view_menu.addAction(
            "&Properties (Ctrl+P)", self.show_properties_page
        )
        self.view_menu.addSeparator()
        self._action_generate_playlist = self.view_menu.addAction(
            "&Generate Playlist (Ctrl+L)", self.videos_page._on_playlist
        )

        # Selection menu (only relevant on videos page)
        self.selection_menu = QMenu("&Selection", self)
        menu_bar.addMenu(self.selection_menu)

        self.selection_menu.addAction(
            "Select &All (Page)\tCtrl+A", self.videos_page._select_all
        )
        self.selection_menu.addAction(
            "Select All in &View\tCtrl+Shift+A", self.videos_page._select_all_in_view
        )
        self.selection_menu.addSeparator()
        self.selection_menu.addAction(
            "&Clear Selection\tEscape", self.videos_page._clear_selection
        )
        self.selection_menu.addSeparator()
        self._action_show_only_selected = self.selection_menu.addAction(
            "Show Only &Selected\tCtrl+Shift+D"
        )
        self._action_show_only_selected.setCheckable(True)
        self._action_show_only_selected.triggered.connect(
            self._on_toggle_show_only_selected
        )
        self.selection_menu.addSeparator()
        self.selection_menu.addAction(
            "&Edit Properties...", self.videos_page._on_batch_edit
        )

        # Options menu
        self.options_menu = QMenu("&Options", self)
        menu_bar.addMenu(self.options_menu)

        # Page size submenu (only relevant on videos page)
        self.page_size_menu = self.options_menu.addMenu("&Page Size")
        self._page_size_group = QActionGroup(self)
        self._page_size_group.setExclusive(True)
        self._page_size_actions = {}
        for size in [10, 20, 50, 100]:
            action = QAction(str(size), self)
            action.setCheckable(True)
            action.setData(size)
            if size == 20:  # Default
                action.setChecked(True)
            self._page_size_group.addAction(action)
            self.page_size_menu.addAction(action)
            self._page_size_actions[size] = action
        self._page_size_group.triggered.connect(self._on_page_size_action)

        self.options_menu.addSeparator()

        # Confirm deletion for entries not found
        self._action_confirm_not_found = self.options_menu.addAction(
            "Confirm &deletion for entries not found"
        )
        self._action_confirm_not_found.setCheckable(True)
        self._action_confirm_not_found.setChecked(True)  # Default: confirm deletions
        self._action_confirm_not_found.setToolTip(
            "When checked, show confirmation dialog before deleting entries not found"
        )
        self._action_confirm_not_found.triggered.connect(
            self._on_confirm_not_found_changed
        )

        # Help menu
        help_menu = QMenu("&Help", self)
        menu_bar.addMenu(help_menu)

        help_menu.addAction("&About", self._show_about)

        # Initial state: database menu disabled
        self._update_database_menu_state()

    def _connect_signals(self):
        """Connect signals from pages and context."""
        # Database page signals
        self.databases_page.database_opening.connect(self._on_database_opening)
        self.databases_page.database_creating.connect(self._on_database_creating)

        # Videos page signals
        self.videos_page.update_database_requested.connect(self._on_update_database)
        self.videos_page.find_similar_requested.connect(self._on_find_similar)
        self.videos_page.move_video_requested.connect(self._on_move_video)
        self.videos_page.status_message_requested.connect(self._on_status_message)

        # Sync "Show Only Selected" menu with button
        self.videos_page.btn_show_only_selected.toggled.connect(
            self._action_show_only_selected.setChecked
        )

        # Context signals
        self.ctx.notification_received.connect(self._on_notification)

    def _on_database_opening(self, name: str, update: bool):
        """Handle database opening request."""
        self._run_process(
            title="Opening Database",
            operation=lambda: self.ctx.open_database(name, update),
            on_end=self._on_database_operation_end,
        )

    def _on_database_creating(self, name: str, folders: list, update: bool):
        """Handle database creation request."""
        self._run_process(
            title="Creating Database",
            operation=lambda: self.ctx.create_database(name, folders, update),
            on_end=self._on_database_operation_end,
        )

    def _on_database_operation_end(self, end_notification: End):
        """Handle database operation completion."""
        self._cleanup_process_page()
        self._update_database_menu_state()
        self.show_videos_page()

    def _on_update_database(self):
        """Handle update database request."""
        self._run_process(
            title="Updating Database",
            operation=lambda: self.ctx.update_database(),
            on_end=self._on_videos_operation_end,
        )

    def _on_find_similar(self):
        """Handle find similar videos request."""
        self._run_process(
            title="Finding Similar Videos",
            operation=lambda: self.ctx.find_similar_videos(),
            on_end=self._on_videos_operation_end,
        )

    def _on_move_video(self, video_id: int, directory: str):
        """Handle move video request."""
        self._run_process(
            title="Moving Video",
            operation=lambda: self.ctx.move_video_file(video_id, directory),
            on_end=self._on_videos_operation_end,
        )

    def _on_videos_operation_end(self, end_notification: End):
        """Handle videos page operation completion."""
        self._cleanup_process_page()
        self.show_videos_page()

    def _on_notification(self, notification):
        """Handle generic notifications (logged separately, not displayed in status bar)."""
        pass

    def _on_status_message(self, message: str, timeout: int = 0):
        """Handle status message requests from pages (timeout=0 means persistent)."""
        self.status_bar.showMessage(message, 0)  # Persistent until clicked or replaced
        self._log_message(message)

    # =========================================================================
    # Session logging
    # =========================================================================

    def _log_session_start(self):
        """Log the session start time."""
        start_str = self._session_start.strftime("%Y-%m-%d %H:%M:%S")
        self._session_log.append(f"{'=' * 60}")
        self._session_log.append(f"Session started: {start_str}")
        self._session_log.append(f"{'=' * 60}")

    def _log_message(self, message: str):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self._session_log.append(entry)
        self._save_log_to_file(entry)

    def _save_log_to_file(self, entry: str):
        """Append a log entry to the session log file in the database folder."""
        if not self.ctx.database:
            return

        db_folder = str(self.ctx.database.ways.db_folder)
        log_file = db_folder + "/session_log.txt"

        # If this is the first write for this session to this database,
        # write the session header first
        if not hasattr(self, "_log_file_initialized"):
            self._log_file_initialized = set()

        db_name = self.ctx.database.get_name()
        if db_name not in self._log_file_initialized:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("\n")
                for header_line in self._session_log[:-1]:  # All but the last entry
                    f.write(header_line + "\n")
            self._log_file_initialized.add(db_name)

        # Append the entry
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def _show_session_log(self):
        """Show the session log dialog."""
        dialog = SessionLogDialog(self._session_log, self)
        dialog.exec()

    def eventFilter(self, obj, event):
        """Clear status bar message on click."""
        if obj is self.status_bar and event.type() == QEvent.Type.MouseButtonPress:
            self.status_bar.clearMessage()
            return True
        return super().eventFilter(obj, event)

    # =========================================================================
    # Process page management
    # =========================================================================

    def _run_process(
        self, title: str, operation: Callable[[], None], on_end: Callable[[End], None]
    ):
        """
        Run an operation with a dedicated ProcessPage.

        Creates a new ProcessPage with its own NotificationCollector,
        displays it, and runs the operation.

        Args:
            title: Title to display on the process page
            operation: Function to call to start the operation
            on_end: Callback when operation ends (receives End notification)
        """
        # Clean up any existing process page
        self._cleanup_process_page()

        # Create new process page
        self._process_page = ProcessPage(title, callback=on_end)

        # Add to stack and display
        self.stack.addWidget(self._process_page)
        self.stack.setCurrentWidget(self._process_page)
        self.setWindowTitle(f"Pysaurus - {title}")

        # Route notifications to the process page
        self.ctx.set_notification_handler(self._process_page)

        # Start the operation
        operation()

    def _cleanup_process_page(self):
        """Remove and clean up the current process page."""
        # Clear notification handler
        self.ctx.clear_notification_handler()

        # Remove process page from stack
        if self._process_page is not None:
            self.stack.removeWidget(self._process_page)
            self._process_page.deleteLater()
            self._process_page = None

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Pysaurus",
            "Pysaurus - Video Collection Manager\n\n"
            "A native Qt6 desktop interface for managing video collections.",
        )

    def _update_menu_state(self):
        """Enable/disable menus based on application state."""
        has_db = self.ctx.database is not None
        on_videos_page = self.stack.currentIndex() == self.PAGE_VIDEOS

        # Database menu: enabled when a database is open
        self.database_menu.setEnabled(has_db)

        # View menu items: Videos/Properties need a database, Playlist needs videos page
        self._action_view_videos.setEnabled(has_db)
        self._action_view_properties.setEnabled(has_db)
        self._action_generate_playlist.setEnabled(has_db and on_videos_page)

        # Selection menu: only relevant on videos page with a database
        self.selection_menu.setEnabled(has_db and on_videos_page)

        # Options menu: Page Size only relevant on videos page
        self.page_size_menu.setEnabled(on_videos_page)

    def _update_database_menu_state(self):
        """Enable/disable database menu based on whether a database is open.

        Deprecated: Use _update_menu_state() instead.
        """
        self._update_menu_state()

    # =========================================================================
    # Database menu actions
    # =========================================================================

    def _on_rename_database(self):
        """Handle rename database action."""
        if not self.ctx.database:
            return

        current_name = self.ctx.database.get_name()
        new_name = RenameDialog.get_name(
            title=f"Rename Database: {current_name}",
            current_name=current_name,
            label="New database name:",
            parent=self,
        )

        if new_name:
            try:
                self.ctx.rename_database(new_name)
                self.setWindowTitle(f"Pysaurus - {new_name}")
                self.status_bar.showMessage(
                    f"Database renamed to '{new_name}'", 3000
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Rename Failed",
                    f"Failed to rename database:\n{e}",
                )

    def _on_edit_folders(self):
        """Handle edit folders action."""
        if not self.ctx.database:
            return

        current_folders = self.ctx.get_database_folders()
        db_name = self.ctx.database.get_name()

        new_folders = EditFoldersDialog.edit_folders(
            folders=current_folders,
            database_name=db_name,
            parent=self,
        )

        if new_folders is not None:
            # Check if folders actually changed
            if set(new_folders) != set(current_folders):
                try:
                    self.ctx.set_database_folders(new_folders)
                    self.status_bar.showMessage("Folders updated", 3000)

                    # Ask if user wants to update the database
                    reply = QMessageBox.question(
                        self,
                        "Update Database",
                        "Folders have been updated.\n\n"
                        "Do you want to scan for new videos now?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes,
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self._on_update_database()
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Update Failed",
                        f"Failed to update folders:\n{e}",
                    )

    def _on_close_database(self):
        """Handle close database action."""
        if not self.ctx.database:
            return

        db_name = self.ctx.database.get_name()
        reply = QMessageBox.question(
            self,
            "Close Database",
            f"Close database '{db_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.ctx.close_database()
            self._update_database_menu_state()
            self.databases_page.refresh()
            self.show_databases_page()

    # =========================================================================
    # Page navigation
    # =========================================================================

    def show_databases_page(self):
        """Navigate to databases page."""
        self.stack.setCurrentIndex(self.PAGE_DATABASES)
        self.setWindowTitle("Pysaurus - Databases")
        self._update_menu_state()

    def show_videos_page(self):
        """Navigate to videos page."""
        if self.ctx.database:
            self.stack.setCurrentIndex(self.PAGE_VIDEOS)
            self.setWindowTitle(f"Pysaurus - {self.ctx.database.get_name()}")
            self.videos_page.refresh()
            self._update_menu_state()
        else:
            self.show_databases_page()

    def show_properties_page(self):
        """Navigate to properties page."""
        if self.ctx.database:
            self.stack.setCurrentIndex(self.PAGE_PROPERTIES)
            self.setWindowTitle(
                f"Pysaurus - Properties - {self.ctx.database.get_name()}"
            )
            self.properties_page.refresh()
            self._update_menu_state()
        else:
            self.show_databases_page()

    # =========================================================================
    # Options menu actions
    # =========================================================================

    def _on_page_size_action(self, action: QAction):
        """Handle page size selection from menu."""
        size = action.data()
        # Update the videos page combo box to match
        self.videos_page.page_size_combo.setCurrentText(str(size))
        # This will trigger the page size change through the combo box signal

    def _on_toggle_show_only_selected(self, checked: bool):
        """Handle show only selected toggle from menu."""
        # Sync the button state in videos_page
        self.videos_page.btn_show_only_selected.setChecked(checked)

    def _on_confirm_not_found_changed(self, checked: bool):
        """Handle confirm deletion setting change."""
        # Store the setting in videos_page
        self.videos_page.confirm_not_found_deletion = checked
        self.status_bar.showMessage(
            f"Confirm deletion for 'not found' entries: {'enabled' if checked else 'disabled'}",
            3000,
        )

    def closeEvent(self, event):
        """Handle window close event."""
        reply = QMessageBox.question(
            self,
            "Quit",
            "Are you sure you want to quit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.ctx.close_app()
            event.accept()
        else:
            event.ignore()
