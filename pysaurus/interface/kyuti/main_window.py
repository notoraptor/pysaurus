"""
Main window for PySide6 interface.

Central window with QStackedWidget for page navigation.
"""

from datetime import datetime
from typing import Callable

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QAction, QActionGroup, QTextCursor
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPlainTextEdit,
    QRadioButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.language import say
from pysaurus.core.notifications import End
from pysaurus.interface.kyuti.app_context import AppContext
from pysaurus.interface.kyuti.dialogs import EditFoldersDialog, RenameDialog
from pysaurus.interface.kyuti.dialogs.process_dialog import ProcessDialog
from pysaurus.interface.kyuti.pages import (
    DatabasesPage,
    FilesPage,
    PropertiesPage,
    VideosPage,
)
from pysaurus.interface.kyuti.pages.process_page import ProcessPage


class SessionLogDialog(QDialog):
    """Dialog to display the session log."""

    def __init__(self, log_entries: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(say("Session Log"))
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
    PAGE_FILES = 3

    def __init__(self):
        super().__init__()
        self.ctx = AppContext()
        self._process_page: ProcessPage | None = None
        self._process_dialog: ProcessDialog | None = None
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
        self.setWindowTitle(say("Pysaurus - Video Collection Manager"))
        self.resize(1200, 800)

        # Central stacked widget for pages
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Create pages
        self.databases_page = DatabasesPage(self.ctx, self)
        self.videos_page = VideosPage(self.ctx, self)
        self.properties_page = PropertiesPage(self.ctx, self)
        self.files_page = FilesPage(self.ctx, self)

        # Add pages to stack
        self.stack.addWidget(self.databases_page)  # Index 0
        self.stack.addWidget(self.videos_page)  # Index 1
        self.stack.addWidget(self.properties_page)  # Index 2
        self.stack.addWidget(self.files_page)  # Index 3

        # Status bar (click to clear message)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(say("Ready"))
        self.status_bar.installEventFilter(self)

    def _setup_menu(self):
        """Set up the menu bar."""
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)

        # Database menu
        self.database_menu = QMenu(say("&Database"), self)
        menu_bar.addMenu(self.database_menu)

        self._action_rename_db = self.database_menu.addAction(
            say("&Rename Database..."), self._on_rename_database
        )
        self._action_edit_folders = self.database_menu.addAction(
            say("&Edit Folders..."), self._on_edit_folders
        )
        self.database_menu.addSeparator()
        self._action_update_db = self.database_menu.addAction(
            say("&Update Database"), self.videos_page._on_update_database
        )
        self.database_menu.addSeparator()
        self._action_find_similar = self.database_menu.addAction(
            say("Find &Similar Videos"), self.videos_page._on_find_similar
        )
        self._action_find_reencoded = self.database_menu.addAction(
            say("Find Re-&encoded Videos"), self.videos_page._on_find_reencoded
        )
        self.database_menu.addSeparator()
        self._action_close_db = self.database_menu.addAction(
            say("&Close Database"), self._on_close_database
        )
        self.database_menu.addSeparator()
        self._action_session_log = self.database_menu.addAction(
            say("Session &Log..."), self._show_session_log
        )
        self._action_quit = self.database_menu.addAction(say("&Quit"), self.close)

        # View menu
        self.view_menu = QMenu(say("&View"), self)
        menu_bar.addMenu(self.view_menu)

        self._action_random_video = self.view_menu.addAction(
            say("&Random Video (Ctrl+O)"), self.videos_page._on_random_video
        )
        self._action_generate_playlist = self.view_menu.addAction(
            say("&Generate Playlist (Ctrl+L)"), self.videos_page._on_playlist
        )
        self.view_menu.addSeparator()
        self._action_refresh_view = self.view_menu.addAction(
            say("Re&fresh View (Ctrl+R)"), self.videos_page.refresh
        )

        # Page navigation radio buttons (right side of menu bar)
        self._page_selector = QWidget()
        page_layout = QHBoxLayout(self._page_selector)
        page_layout.setContentsMargins(0, 0, 4, 0)
        page_layout.setSpacing(8)
        self._radio_videos = QRadioButton(say("Videos"))
        self._radio_properties = QRadioButton(say("Properties"))
        self._radio_files = QRadioButton(say("Files"))
        self._page_button_group = QButtonGroup(self)
        self._page_button_group.addButton(self._radio_videos, self.PAGE_VIDEOS)
        self._page_button_group.addButton(self._radio_properties, self.PAGE_PROPERTIES)
        self._page_button_group.addButton(self._radio_files, self.PAGE_FILES)
        page_layout.addWidget(self._radio_videos)
        page_layout.addWidget(self._radio_properties)
        page_layout.addWidget(self._radio_files)
        self._page_button_group.idClicked.connect(self._on_page_radio_clicked)
        menu_bar.setCornerWidget(self._page_selector, Qt.Corner.TopRightCorner)

        # Options menu
        self.options_menu = QMenu(say("&Options"), self)
        menu_bar.addMenu(self.options_menu)

        # Page size submenu
        self.page_size_menu = self.options_menu.addMenu(say("&Page Size"))
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
            say("Confirm &deletion for entries not found")
        )
        self._action_confirm_not_found.setCheckable(True)
        self._action_confirm_not_found.setChecked(True)  # Default: confirm deletions
        self._action_confirm_not_found.setToolTip(
            say(
                "When checked, show confirmation dialog before deleting entries"
                " not found"
            )
        )
        self._action_confirm_not_found.triggered.connect(
            self._on_confirm_not_found_changed
        )

        self.options_menu.addSeparator()

        # Language submenu (one exclusive checkable action per available code)
        self.language_menu = self.options_menu.addMenu(say("&Language"))
        self._language_group = QActionGroup(self)
        self._language_group.setExclusive(True)
        current_language = self.ctx.get_current_language()
        for code in self.ctx.get_available_languages():
            action = QAction(self.ctx.get_language_display_name(code), self)
            action.setCheckable(True)
            action.setData(code)
            if code == current_language:
                action.setChecked(True)
            self._language_group.addAction(action)
            self.language_menu.addAction(action)
        self._language_group.triggered.connect(self._on_language_action)

        # Help menu
        self.help_menu = QMenu(say("&Help"), self)
        menu_bar.addMenu(self.help_menu)

        self._action_about = self.help_menu.addAction(say("&About"), self._show_about)

        # Initial state: database menu disabled
        self._update_database_menu_state()

    def retranslateUi(self):
        """Re-apply the text of every *static* piece of chrome in the current
        language. Triggered by QEvent.LanguageChange (see changeEvent).

        The construction keeps its say() calls (the text stays readable at the
        call site), so this only *repeats* them for the persistent menu bar; it
        is deliberately NOT called at startup. Dynamic page content is
        retranslated on its own by refresh() via the state_changed signal.
        """
        # Menu titles
        self.database_menu.setTitle(say("&Database"))
        self.view_menu.setTitle(say("&View"))
        self.options_menu.setTitle(say("&Options"))
        self.page_size_menu.setTitle(say("&Page Size"))
        self.language_menu.setTitle(say("&Language"))
        self.help_menu.setTitle(say("&Help"))
        # Database menu actions
        self._action_rename_db.setText(say("&Rename Database..."))
        self._action_edit_folders.setText(say("&Edit Folders..."))
        self._action_update_db.setText(say("&Update Database"))
        self._action_find_similar.setText(say("Find &Similar Videos"))
        self._action_find_reencoded.setText(say("Find Re-&encoded Videos"))
        self._action_close_db.setText(say("&Close Database"))
        self._action_session_log.setText(say("Session &Log..."))
        self._action_quit.setText(say("&Quit"))
        # View menu actions
        self._action_random_video.setText(say("&Random Video (Ctrl+O)"))
        self._action_generate_playlist.setText(say("&Generate Playlist (Ctrl+L)"))
        self._action_refresh_view.setText(say("Re&fresh View (Ctrl+R)"))
        # Page selector radios
        self._radio_videos.setText(say("Videos"))
        self._radio_properties.setText(say("Properties"))
        self._radio_files.setText(say("Files"))
        # Options menu
        self._action_confirm_not_found.setText(
            say("Confirm &deletion for entries not found")
        )
        self._action_confirm_not_found.setToolTip(
            say(
                "When checked, show confirmation dialog before deleting entries"
                " not found"
            )
        )
        # Help menu
        self._action_about.setText(say("&About"))
        # Window title depends on the current page
        self._update_window_title()

    def changeEvent(self, event):
        """Qt posts LanguageChange to every widget when a QTranslator is
        installed or removed. That is our cue to re-pull the static chrome."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def _update_window_title(self):
        """Set the window title from the current page — single source of truth,
        shared by the show_*_page navigation and by retranslateUi()."""
        index = self.stack.currentIndex()
        if index == self.PAGE_DATABASES:
            self.setWindowTitle(say("Pysaurus - Databases"))
        elif index == self.PAGE_VIDEOS:
            self.setWindowTitle(
                say("Pysaurus - {name}", name=self.ctx.get_database_name())
            )
        elif index == self.PAGE_PROPERTIES:
            self.setWindowTitle(
                say("Pysaurus - Properties - {name}", name=self.ctx.get_database_name())
            )
        elif index == self.PAGE_FILES:
            self.setWindowTitle(
                say("Pysaurus - Files - {name}", name=self.ctx.get_database_name())
            )

    def _connect_signals(self):
        """Connect signals from pages and context."""
        # Database page signals
        self.databases_page.database_opening.connect(self._on_database_opening)
        self.databases_page.database_creating.connect(self._on_database_creating)

        # Videos page signals
        self.videos_page.update_database_requested.connect(self._on_update_database)
        self.videos_page.find_similar_requested.connect(self._on_find_similar)
        self.videos_page.find_similar_reencoded_requested.connect(
            self._on_find_similar_reencoded
        )
        self.videos_page.move_video_requested.connect(self._on_move_video)
        self.videos_page.status_message_requested.connect(self._on_status_message)

        # Files page signals
        self.files_page.scan_requested.connect(self._on_scan_folders)

        # Context signals
        self.ctx.notification_received.connect(self._on_notification)
        self.ctx.state_changed.connect(self._on_state_changed)

    def _on_database_opening(self, name: str, update: bool):
        """Handle database opening request."""
        self._run_process(
            title=say("Opening Database"),
            operation=lambda: self.ctx.open_database(name, update),
            on_end=self._on_database_operation_end,
            autocontinue=not update,
        )

    def _on_database_creating(self, name: str, folders: list, update: bool):
        """Handle database creation request."""
        self._run_process(
            title=say("Creating Database"),
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
            title=say("Updating Database"),
            operation=lambda: self.ctx.update_database(),
            on_end=self._on_videos_operation_end_reset_selection,
        )

    def _on_find_similar(self):
        """Handle find similar videos request."""
        self._run_process(
            title=say("Finding Similar Videos"),
            operation=lambda: self.ctx.find_similar_videos(),
            on_end=self._on_videos_operation_end_reset_selection,
        )

    def _on_find_similar_reencoded(self):
        """Handle find re-encoded videos request."""
        self._run_process(
            title=say("Finding Re-encoded Videos"),
            operation=lambda: self.ctx.find_similar_videos_reencoded(),
            on_end=self._on_videos_operation_end_reset_selection,
        )

    def _on_move_video(self, video_id: int, directory: str):
        """Handle move video request."""
        self._run_process_modal(
            title=say("Moving Video"),
            operation=lambda: self.ctx.move_video_file(video_id, directory),
            on_end=self._on_videos_operation_end,
        )

    def _on_videos_operation_end(self, end_notification: End):
        """Handle videos page operation completion."""
        self._cleanup_process_page()
        self.show_videos_page()

    def _on_videos_operation_end_reset_selection(self, end_notification: End):
        """Handle completion of an operation that changes the video set (update, find similar/re-encoded), clearing the now possibly-stale selection."""
        self.videos_page._clear_selection()
        self._on_videos_operation_end(end_notification)

    def _on_scan_folders(self):
        """Handle scan folders request from the files page."""
        self._run_process(
            title=say("Scanning Folders"),
            operation=lambda: self.ctx.scan_folders(),
            on_end=self._on_scan_folders_end,
        )

    def _on_scan_folders_end(self, end_notification: End):
        """Handle scan folders completion."""
        self._cleanup_process_page()
        self.show_files_page()

    def _on_notification(self, notification):
        """Handle generic notifications (logged separately, not displayed in status bar)."""
        pass

    def _on_state_changed(self):
        """Refresh the active page when backend state changes."""
        if self._process_page is not None:
            return  # a process is running; pages are refreshed when it ends
        current = self.stack.currentIndex()
        if current == self.PAGE_VIDEOS:
            self.videos_page.refresh()
        elif current == self.PAGE_PROPERTIES:
            self.properties_page.refresh()
        elif current == self.PAGE_DATABASES:
            self.databases_page.refresh()
        elif current == self.PAGE_FILES:
            self.files_page.refresh()

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
        self._session_log.append(say("Session started: {time}", time=start_str))
        self._session_log.append(f"{'=' * 60}")

    def _log_message(self, message: str):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self._session_log.append(entry)
        self._save_log_to_file(entry)

    def _save_log_to_file(self, entry: str):
        """Append a log entry to the session log file in the database folder."""
        if not self.ctx.has_database():
            return

        db_folder = self.ctx.get_database_folder_path()
        log_file = db_folder + "/session_log.txt"

        # If this is the first write for this session to this database,
        # write the session header first
        if not hasattr(self, "_log_file_initialized"):
            self._log_file_initialized = set()

        db_name = self.ctx.get_database_name()
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
        self,
        title: str,
        operation: Callable[[], None],
        on_end: Callable[[End], None],
        autocontinue: bool = False,
    ):
        """
        Run an operation with a dedicated ProcessPage.

        Creates a new ProcessPage with its own NotificationCollector,
        displays it, and runs the operation.

        Args:
            title: Title to display on the process page
            operation: Function to call to start the operation
            on_end: Callback when operation ends (receives End notification)
            autocontinue: If True, skip the Continue button and proceed immediately
        """
        if self._process_page is not None:
            return  # Already running a process

        # Clean up any existing process page
        self._cleanup_process_page()

        # Create new process page
        self._process_page = ProcessPage(
            title, callback=on_end, autocontinue=autocontinue
        )

        # Add to stack and display
        self.stack.addWidget(self._process_page)
        self.stack.setCurrentWidget(self._process_page)
        self.setWindowTitle(f"Pysaurus - {title}")

        # Disable menus and navigation while processing
        self._update_menu_state()

        # Route notifications to the process page
        self.ctx.set_notification_handler(self._process_page)

        # Start the operation
        operation()

    def _run_process_modal(
        self, title: str, operation: Callable[[], None], on_end: Callable[[End], None]
    ):
        """
        Run an operation with a ProcessPage hosted in an application-modal dialog.

        Same contract as _run_process(), except the current page stays visible
        (but inert) below the dialog instead of being swapped out.
        """
        if self._process_page is not None:
            return  # Already running a process

        self._cleanup_process_page()

        self._process_dialog = ProcessDialog(title, callback=on_end, parent=self)
        self._process_page = self._process_dialog.page

        # Modality already blocks the window below, so menus are left as-is.
        self.ctx.set_notification_handler(self._process_page)
        self._process_dialog.show()

        try:
            operation()
        except Exception:
            # No End notification will ever come: close the dialog, else the
            # modality leaves the whole window stuck.
            self._cleanup_process_page()
            raise

    def _cleanup_process_page(self):
        """Remove and clean up the current process page (or its modal dialog)."""
        # Clear notification handler
        self.ctx.clear_notification_handler()

        if self._process_dialog is not None:
            # hide(), not close(): closeEvent is routed back to Continue.
            self._process_dialog.hide()
            self._process_dialog.deleteLater()
            self._process_dialog = None
            self._process_page = None
        elif self._process_page is not None:
            self.stack.removeWidget(self._process_page)
            self._process_page.deleteLater()
            self._process_page = None

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            say("About Pysaurus"),
            say(
                "Pysaurus - Video Collection Manager\n\n"
                "A native Qt6 desktop interface for managing video collections."
            ),
        )

    def _update_menu_state(self):
        """Enable/disable menus based on application state."""
        processing = self._process_page is not None
        has_db = not processing and self.ctx.has_database()
        current_page = self.stack.currentIndex()
        on_videos_page = not processing and current_page == self.PAGE_VIDEOS

        # Database menu actions: enabled when a database is open
        self._action_rename_db.setEnabled(has_db)
        self._action_edit_folders.setEnabled(has_db)
        self._action_update_db.setEnabled(has_db)
        self._action_find_similar.setEnabled(has_db)
        self._action_find_reencoded.setEnabled(has_db)
        self._action_close_db.setEnabled(has_db)
        self._action_session_log.setEnabled(has_db)

        # View menu: enabled when on videos page
        self.view_menu.setEnabled(has_db and on_videos_page)

        # Options menu is reachable without an open database (so the Language
        # submenu — an app-global setting — can be changed from the home page),
        # but NOT during a process: switching language installs a QTranslator
        # that posts LanguageChange to the ProcessPage, which has no
        # retranslateUi. Its database-specific children are gated individually.
        self.options_menu.setEnabled(not processing)
        self.page_size_menu.setEnabled(on_videos_page)
        self._action_confirm_not_found.setEnabled(has_db)

        # Page selector radio buttons: hidden during processing
        self._page_selector.setVisible(has_db)
        if has_db and current_page in (
            self.PAGE_VIDEOS,
            self.PAGE_PROPERTIES,
            self.PAGE_FILES,
        ):
            self._page_button_group.blockSignals(True)
            self._page_button_group.button(current_page).setChecked(True)
            self._page_button_group.blockSignals(False)

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
        if not self.ctx.has_database():
            return

        current_name = self.ctx.get_database_name()
        new_name = RenameDialog.get_name(
            title=say("Rename Database: {name}", name=current_name),
            current_name=current_name,
            label=say("New database name:"),
            parent=self,
        )

        if new_name:
            try:
                self.ctx.rename_database(new_name)
                self._update_window_title()
                self.status_bar.showMessage(
                    say("Database renamed to '{name}'", name=new_name), 3000
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    say("Rename Failed"),
                    say("Failed to rename database:\n{error}", error=e),
                )

    def _on_edit_folders(self):
        """Handle edit folders action."""
        if not self.ctx.has_database():
            return

        current_folders = self.ctx.get_database_folders()
        db_name = self.ctx.get_database_name()

        new_folders = EditFoldersDialog.edit_folders(
            folders=current_folders, database_name=db_name, parent=self
        )

        if new_folders is not None:
            # Check if folders actually changed
            if set(new_folders) != set(current_folders):
                try:
                    self.ctx.set_database_folders(new_folders)
                    self.status_bar.showMessage(say("Folders updated"), 3000)

                    # Ask if user wants to update the database
                    reply = QMessageBox.question(
                        self,
                        say("Update Database"),
                        say(
                            "Folders have been updated.\n\n"
                            "Do you want to scan for new videos now?"
                        ),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes,
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self._on_update_database()
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        say("Update Failed"),
                        say("Failed to update folders:\n{error}", error=e),
                    )

    def _on_close_database(self):
        """Handle close database action."""
        if not self.ctx.has_database():
            return

        db_name = self.ctx.get_database_name()
        reply = QMessageBox.question(
            self,
            say("Close Database"),
            say("Close database '{name}'?", name=db_name),
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

    def _on_page_radio_clicked(self, page_id: int):
        """Handle page selector radio button click."""
        if page_id == self.PAGE_VIDEOS:
            self.show_videos_page()
        elif page_id == self.PAGE_PROPERTIES:
            self.show_properties_page()
        elif page_id == self.PAGE_FILES:
            self.show_files_page()

    def show_databases_page(self):
        """Navigate to databases page."""
        self.stack.setCurrentIndex(self.PAGE_DATABASES)
        self._update_window_title()
        self._update_menu_state()

    def show_videos_page(self):
        """Navigate to videos page."""
        if self.ctx.has_database():
            self.stack.setCurrentIndex(self.PAGE_VIDEOS)
            self._update_window_title()
            self.videos_page.refresh()
            self._update_menu_state()
        else:
            self.show_databases_page()

    def show_properties_page(self):
        """Navigate to properties page."""
        if self.ctx.has_database():
            self.stack.setCurrentIndex(self.PAGE_PROPERTIES)
            self._update_window_title()
            self.properties_page.refresh()
            self._update_menu_state()
        else:
            self.show_databases_page()

    def show_files_page(self):
        """Navigate to the files page (DB file inventory)."""
        if self.ctx.has_database():
            self.stack.setCurrentIndex(self.PAGE_FILES)
            self._update_window_title()
            self.files_page.refresh()
            self._update_menu_state()
        else:
            self.show_databases_page()

    # =========================================================================
    # Options menu actions
    # =========================================================================

    def _on_page_size_action(self, action: QAction):
        """Handle page size selection from menu."""
        self.videos_page._on_page_size_changed(str(action.data()))

    def _on_confirm_not_found_changed(self, checked: bool):
        """Handle confirm deletion setting change."""
        # Store the setting in videos_page
        self.videos_page.confirm_not_found_deletion = checked
        state = say("enabled") if checked else say("disabled")
        self.status_bar.showMessage(
            say("Confirm deletion for 'not found' entries: {state}", state=state), 3000
        )

    def _on_language_action(self, action: QAction):
        """Handle language selection. The switch is applied live: set_language
        installs the Qt translator — which posts LanguageChange to every widget,
        so each retranslateUi() re-pulls its static text — and emits
        state_changed, which refreshes the active page's dynamic content."""
        code = action.data()
        if code == self.ctx.get_current_language():
            return
        self.ctx.set_language(code)

    def closeEvent(self, event):
        """Handle window close event."""
        reply = QMessageBox.question(
            self,
            say("Quit"),
            say("Are you sure you want to quit?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.ctx.close_app()
            event.accept()
        else:
            event.ignore()
