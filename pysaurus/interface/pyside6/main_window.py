"""
Main window for PySide6 interface.

Central window with QStackedWidget for page navigation.
"""

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QStatusBar, QMenuBar, QMenu

from pysaurus.interface.pyside6.app_context import AppContext
from pysaurus.interface.pyside6.pages import (
    DatabasesPage,
    HomePage,
    PropertiesPage,
    VideosPage,
)


class MainWindow(QMainWindow):
    """
    Main application window.

    Contains:
    - Menu bar (File, View, Help)
    - Central QStackedWidget for page navigation
    - Status bar
    """

    # Page indices
    PAGE_DATABASES = 0
    PAGE_HOME = 1
    PAGE_VIDEOS = 2
    PAGE_PROPERTIES = 3

    def __init__(self):
        super().__init__()
        self.ctx = AppContext()
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
        self.home_page = HomePage(self.ctx, self)
        self.videos_page = VideosPage(self.ctx, self)
        self.properties_page = PropertiesPage(self.ctx, self)

        # Add pages to stack
        self.stack.addWidget(self.databases_page)  # Index 0
        self.stack.addWidget(self.home_page)  # Index 1
        self.stack.addWidget(self.videos_page)  # Index 2
        self.stack.addWidget(self.properties_page)  # Index 3

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

        # Help menu
        help_menu = QMenu("&Help", self)
        menu_bar.addMenu(help_menu)

        help_menu.addAction("&About", self._show_about)

    def _connect_signals(self):
        """Connect signals from pages and context."""
        # Database page signals
        self.databases_page.database_opening.connect(self._on_database_opening)
        self.databases_page.database_creating.connect(self._on_database_creating)

        # Home page signals
        self.home_page.continue_requested.connect(self._on_continue_to_videos)

        # Videos page signals
        self.videos_page.long_operation_requested.connect(self._on_long_operation)

        # Context signals
        self.ctx.database_ready.connect(self._on_database_ready)
        self.ctx.notification_received.connect(self._on_notification)

    def _on_database_opening(self, name: str, update: bool):
        """Handle database opening request."""
        self.home_page.reset()
        self.show_home_page()
        self.ctx.open_database(name, update)

    def _on_database_creating(self, name: str, folders: list, update: bool):
        """Handle database creation request."""
        self.home_page.reset()
        self.show_home_page()
        self.ctx.create_database(name, folders, update)

    def _on_database_ready(self):
        """Handle database ready notification."""
        # Don't navigate automatically - let user click Continue
        self.status_bar.showMessage(f"Database loaded: {self.ctx.database.get_name()}")

    def _on_continue_to_videos(self):
        """Handle continue button from home page."""
        self.show_videos_page()

    def _on_long_operation(self):
        """Handle request to show home page for long operation."""
        self.home_page.reset()
        self.show_home_page()

    def _on_notification(self, notification):
        """Handle generic notifications."""
        self.status_bar.showMessage(str(notification), 3000)

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

    def show_home_page(self):
        """Navigate to home page (loading progress)."""
        self.stack.setCurrentIndex(self.PAGE_HOME)
        self.setWindowTitle("Pysaurus - Loading...")

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
