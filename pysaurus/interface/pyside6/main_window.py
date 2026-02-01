"""
Main window for PySide6 interface.

Central window with QStackedWidget for page navigation.
"""

from typing import Callable

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QStatusBar, QMenuBar, QMenu

from pysaurus.core.notifications import End
from pysaurus.interface.pyside6.app_context import AppContext
from pysaurus.interface.pyside6.pages import (
    DatabasesPage,
    PropertiesPage,
    VideosPage,
)
from pysaurus.interface.pyside6.pages.process_page import ProcessPage


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
        self._setup_ui()
        self._setup_menu()
        self._connect_signals()

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

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Start on databases page
        self.show_databases_page()

    def _setup_menu(self):
        """Set up the menu bar."""
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)

        # File menu
        file_menu = QMenu("&File", self)
        menu_bar.addMenu(file_menu)

        file_menu.addAction("&Databases", self.show_databases_page)
        file_menu.addSeparator()
        file_menu.addAction("&Quit", self.close)

        # View menu
        view_menu = QMenu("&View", self)
        menu_bar.addMenu(view_menu)

        view_menu.addAction("&Videos", self.show_videos_page)
        view_menu.addAction("&Properties", self.show_properties_page)
        view_menu.addSeparator()
        view_menu.addAction("&Generate Playlist (Ctrl+L)", self.videos_page._on_playlist)

        # Help menu
        help_menu = QMenu("&Help", self)
        menu_bar.addMenu(help_menu)

        help_menu.addAction("&About", self._show_about)

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
        """Handle generic notifications."""
        self.status_bar.showMessage(str(notification), 3000)

    def _on_status_message(self, message: str, timeout: int):
        """Handle status message requests from pages."""
        self.status_bar.showMessage(message, timeout)

    # =========================================================================
    # Process page management
    # =========================================================================

    def _run_process(
        self,
        title: str,
        operation: Callable[[], None],
        on_end: Callable[[End], None],
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
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.about(
            self,
            "About Pysaurus",
            "Pysaurus - Video Collection Manager\n\n"
            "A native Qt6 desktop interface for managing video collections.",
        )

    # =========================================================================
    # Page navigation
    # =========================================================================

    def show_databases_page(self):
        """Navigate to databases page."""
        self.stack.setCurrentIndex(self.PAGE_DATABASES)
        self.setWindowTitle("Pysaurus - Databases")

    def show_videos_page(self):
        """Navigate to videos page."""
        if self.ctx.database:
            self.stack.setCurrentIndex(self.PAGE_VIDEOS)
            self.setWindowTitle(f"Pysaurus - {self.ctx.database.get_name()}")
            self.videos_page.refresh()
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
        else:
            self.show_databases_page()

    def closeEvent(self, event):
        """Handle window close event."""
        self.ctx.close_app()
        event.accept()
