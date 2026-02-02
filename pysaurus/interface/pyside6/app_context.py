"""
Application context for PySide6 interface.

Wraps PySide6API and provides Qt signals for backend notifications.
"""

from PySide6.QtCore import QObject, Qt, Signal, Slot

from pysaurus.core.job_notifications import JobStep, JobToDo
from pysaurus.core.notifications import (
    Cancelled,
    DatabaseReady,
    Done,
    End,
    Notification,
    ProfilingEnd,
    ProfilingStart,
)
from pysaurus.interface.pyside6.pyside6_api import PySide6API
from pysaurus.video.video_search_context import VideoSearchContext


class AppContext(QObject):
    """
    Application context shared between all pages.

    Wraps PySide6API and exposes Qt signals for backend notifications.
    Provides direct access to database layers without JSON serialization.
    """

    # Internal signal for thread-safe notification delivery
    # (emitted from background thread, received in main thread)
    _notification_from_thread = Signal(object)

    # Public Qt signals for backend notifications
    notification_received = Signal(object)  # Notification (any type)
    database_ready = Signal()  # DatabaseReady
    profiling_started = Signal(str)  # ProfilingStart: (name)
    profiling_ended = Signal(str, str)  # ProfilingEnd: (name, time)
    operation_done = Signal()  # Done
    operation_cancelled = Signal()  # Cancelled
    operation_ended = Signal(str)  # End: (message)
    job_started = Signal(str, int, str)  # JobToDo: (name, total, title)
    job_progress = Signal(
        str, str, int, int, str
    )  # JobStep: (name, channel, step, total, title)

    def __init__(self):
        super().__init__()
        self.api = PySide6API()

        # Current notification handler (e.g., ProcessPage)
        # When set, notifications are routed to this handler instead of signals
        self._notification_handler = None

        # Connect internal signal with QueuedConnection for thread safety
        self._notification_from_thread.connect(
            self._process_notification, Qt.ConnectionType.QueuedConnection
        )

        # Set callback to emit the internal signal from background thread
        self.api.set_notification_callback(self._on_notification_from_thread)

    def set_notification_handler(self, handler):
        """
        Set the current notification handler.

        When set, notifications are routed to handler.on_notification()
        instead of emitting individual signals.

        Args:
            handler: Object with on_notification(notification) method, or None
        """
        self._notification_handler = handler

    def clear_notification_handler(self):
        """Clear the current notification handler."""
        self._notification_handler = None

    def _on_notification_from_thread(self, notification: Notification):
        """
        Called from background thread.
        Emits internal signal to safely transfer to main thread.
        """
        self._notification_from_thread.emit(notification)

    @Slot(object)
    def _process_notification(self, notification: Notification):
        """
        Process notification in the main thread.

        If a notification handler is set, routes to it.
        Otherwise, emits public signals for UI components.
        """
        # Route to handler if set
        if self._notification_handler is not None:
            self._notification_handler.on_notification(notification)
            # Also emit generic signal for status bar, etc.
            self.notification_received.emit(notification)
            return

        # Generic signal for all notifications
        self.notification_received.emit(notification)

        # Specific signals for common notification types
        if isinstance(notification, DatabaseReady):
            self.database_ready.emit()
        elif isinstance(notification, ProfilingStart):
            self.profiling_started.emit(notification.name)
        elif isinstance(notification, ProfilingEnd):
            self.profiling_ended.emit(notification.name, notification.time)
        elif isinstance(notification, Done):
            self.operation_done.emit()
        elif isinstance(notification, Cancelled):
            self.operation_cancelled.emit()
        elif isinstance(notification, End):
            self.operation_ended.emit(notification.message)
        elif isinstance(notification, JobToDo):
            self.job_started.emit(
                notification.name, notification.total, notification.title or ""
            )
        elif isinstance(notification, JobStep):
            # Convert channel to string, handling None and 0 correctly
            channel = "" if notification.channel is None else str(notification.channel)
            self.job_progress.emit(
                notification.name,
                channel,
                notification.step,
                notification.total,
                notification.title or "",
            )

    # =========================================================================
    # Direct access to layers (no JSON serialization)
    # =========================================================================

    @property
    def database(self):
        """AbstractDatabase or None."""
        return self.api.database

    @property
    def provider(self):
        """VideoProvider or None."""
        return self.database.provider if self.database else None

    @property
    def ops(self):
        """DatabaseOperations or None."""
        return self.database.ops if self.database else None

    @property
    def algos(self):
        """DatabaseAlgorithms or None."""
        return self.database.algos if self.database else None

    @property
    def application(self):
        """Application instance."""
        return self.api.application

    # =========================================================================
    # Long operations (via @process in GuiAPI, executed in thread)
    # =========================================================================

    def get_database_names(self) -> list[str]:
        """List of database names."""
        return self.api.application.get_database_names()

    def create_database(
        self, name: str, folders: list[str], update: bool = True
    ) -> None:
        """Create a database (threaded). Emits database_ready when done."""
        self.api.create_database(name, folders, update)

    def open_database(self, name: str, update: bool = True) -> None:
        """Open a database (threaded). Emits database_ready when done."""
        self.api.open_database(name, update)

    def update_database(self) -> None:
        """Refresh the database (threaded). Emits database_ready when done."""
        self.api.update_database()

    def find_similar_videos(self) -> None:
        """Find similar videos (threaded). Emits database_ready when done."""
        self.api.find_similar_videos()

    def move_video_file(self, video_id: int, directory: str) -> None:
        """Move a video file (threaded). Emits done/cancelled/ended."""
        self.api.move_video_file(video_id, directory)

    def cancel_operation(self) -> None:
        """Cancel the current operation."""
        self.api.cancel_copy()

    # =========================================================================
    # Synchronous operations (direct access, no threading)
    # =========================================================================

    def get_videos(self, page_size: int, page_number: int) -> VideoSearchContext:
        """Return the context with videos (list[VideoPattern])."""
        return self.provider.get_current_state(page_size, page_number)

    def close_database(self) -> None:
        """Close the database."""
        self.api.close_database()

    def delete_database(self) -> None:
        """Delete the database."""
        self.api.delete_database()

    def rename_database(self, new_name: str) -> None:
        """Rename the database and update the application registry."""
        if self.database:
            # Get old path before renaming
            old_path = self.database.ways.db_folder
            # Perform the rename (this changes ways.db_folder)
            self.database.rename(new_name)
            # Get new path after renaming
            new_path = self.database.ways.db_folder
            # Update Application.databases dictionary
            if old_path in self.application.databases:
                del self.application.databases[old_path]
                self.application.databases[new_path] = self.database

    def get_database_folders(self) -> list[str]:
        """Get the database source folders."""
        if self.database:
            return [str(f) for f in self.database.get_folders()]
        return []

    def set_database_folders(self, folders: list[str]) -> None:
        """Set the database source folders."""
        if self.ops:
            self.ops.set_folders(folders)

    def close_app(self) -> None:
        """Close the application properly."""
        self.api.close_app()
