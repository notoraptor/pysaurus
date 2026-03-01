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
from pysaurus.video.video_pattern import VideoPattern
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

    # Internal signal for thread-safe exception delivery
    # (emitted from background thread, received in main thread)
    _exception_from_thread = Signal(object)

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
    state_changed = Signal()  # Emitted after any state-mutating facade method

    def __init__(self):
        super().__init__()
        self._api = PySide6API()

        # Current notification handler (e.g., ProcessPage)
        # When set, notifications are routed to this handler instead of signals
        self._notification_handler = None

        # Connect internal signal with QueuedConnection for thread safety
        self._notification_from_thread.connect(
            self._process_notification, Qt.ConnectionType.QueuedConnection
        )

        # Connect exception signal to re-raise in main thread
        self._exception_from_thread.connect(
            self._handle_exception, Qt.ConnectionType.QueuedConnection
        )

        # Set callback to emit the internal signal from background thread
        self._api.set_notification_callback(self._on_notification_from_thread)

        # Set callback for exceptions from background threads
        self._api.set_exception_callback(self._on_exception_from_thread)

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

    def _on_exception_from_thread(self, exception):
        """Called from background thread. Emits signal to transfer to main thread."""
        self._exception_from_thread.emit(exception)

    @Slot(object)
    def _handle_exception(self, exception):
        """Called in the main thread. Re-raises so that sys.excepthook intercepts it."""
        raise exception

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
    # Private access to layers (no JSON serialization)
    # =========================================================================

    @property
    def _database(self):
        """AbstractDatabase or None."""
        return self._api.database

    @property
    def _provider(self):
        """VideoProvider or None."""
        return self._database.provider if self._database else None

    @property
    def _ops(self):
        """DatabaseOperations or None."""
        return self._database.ops if self._database else None

    @property
    def _algos(self):
        """DatabaseAlgorithms or None."""
        return self._database.algos if self._database else None

    @property
    def _application(self):
        """Application instance."""
        return self._api.application

    # =========================================================================
    # Long operations (via @process in GuiAPI, executed in thread)
    # =========================================================================

    def get_database_names(self) -> list[str]:
        """List of database names."""
        return self._api.application.get_database_names()

    def create_database(
        self, name: str, folders: list[str], update: bool = True
    ) -> None:
        """Create a database (threaded). Emits database_ready when done."""
        self._api.create_database(name, folders, update)

    def open_database(self, name: str, update: bool = True) -> None:
        """Open a database (threaded). Emits database_ready when done."""
        self._api.open_database(name, update)

    def update_database(self) -> None:
        """Refresh the database (threaded). Emits database_ready when done."""
        self._api.update_database()

    def find_similar_videos(self) -> None:
        """Find similar videos (threaded). Emits database_ready when done."""
        self._api.find_similar_videos()

    def move_video_file(self, video_id: int, directory: str) -> None:
        """Move a video file (threaded). Emits done/cancelled/ended."""
        self._api.move_video_file(video_id, directory)

    def cancel_operation(self) -> None:
        """Cancel the current operation."""
        self._api.cancel_copy()

    # =========================================================================
    # Synchronous operations (direct access, no threading)
    # =========================================================================

    def get_videos(
        self, page_size: int, page_number: int, selector=None
    ) -> VideoSearchContext:
        """Return the context with videos (list[VideoPattern])."""
        return self._provider.get_current_state(page_size, page_number, selector)

    def close_database(self) -> None:
        """Close the database."""
        self._api.close_database()

    def delete_database(self) -> None:
        """Delete the database."""
        self._api.delete_database()

    def rename_database(self, new_name: str) -> None:
        """Rename the database and update the application registry."""
        if self._database:
            # Get old path before renaming
            old_path = self._database.ways.db_folder
            # Perform the rename (this changes ways.db_folder)
            self._database.rename(new_name)
            # Get new path after renaming
            new_path = self._database.ways.db_folder
            # Update Application.databases dictionary
            if old_path in self._application.databases:
                del self._application.databases[old_path]
                self._application.databases[new_path] = self._database
            self.state_changed.emit()

    def get_database_folders(self) -> list[str]:
        """Get the database source folders."""
        if self._database:
            return [str(f) for f in self._database.get_folders()]
        return []

    def set_database_folders(self, folders: list[str]) -> None:
        """Set the database source folders."""
        if self._ops:
            self._ops.set_folders(folders)
            self.state_changed.emit()

    def confirm_move(self, src_video_id: int, dst_video_id: int) -> None:
        """Confirm a video move (transfer metadata from src to dst, delete src)."""
        if self._ops:
            self._ops.move_video_entry(src_video_id, dst_video_id)
            self.state_changed.emit()

    def confirm_unique_moves(self) -> int:
        """Confirm all unique video moves (1-to-1 mappings). Returns count."""
        if self._algos:
            result = self._algos.confirm_unique_moves()
            self.state_changed.emit()
            return result
        return 0

    # =========================================================================
    # Classifier operations
    # =========================================================================

    def classifier_select_group(self, group_id: int) -> None:
        """Add a group value to the classifier path."""
        if self._provider:
            self._provider.classifier_select_group(group_id)
            self.state_changed.emit()

    def classifier_back(self) -> None:
        """Remove the last value from the classifier path."""
        if self._provider:
            self._provider.classifier_back()
            self.state_changed.emit()

    def classifier_reverse(self) -> list:
        """Reverse the classifier path order. Returns the new path."""
        if self._provider:
            result = self._provider.classifier_reverse()
            self.state_changed.emit()
            return result
        return []

    def classifier_concatenate_path(self, to_property: str) -> None:
        """
        Concatenate the classifier path values into a string property.

        Joins all path values with spaces and moves them to the target property.
        Clears the classifier path after concatenation.
        """
        if self._provider and self._algos:
            path = self._provider.get_classifier_path()
            from_property = self._provider.get_grouping().field
            self._provider.set_classifier_path([])
            self._provider.set_group(0)
            self._algos.move_property_values(
                path, from_property, to_property, concatenate=True
            )
            self.state_changed.emit()

    def classifier_focus_prop_val(self, prop_name: str, field_value) -> None:
        """Focus on a specific property value (resets classifier and jumps to value)."""
        if self._provider:
            self._provider.classifier_focus_prop_val(prop_name, field_value)
            self.state_changed.emit()

    # =========================================================================
    # View operations with selector
    # =========================================================================

    def query_on_view(self, selector_dict: dict, operation: str, *args):
        """Query the current view without modifying state (no state_changed)."""
        if self._provider:
            return self._provider.apply_on_view(selector_dict, operation, *args)
        return None

    def apply_on_view(self, selector_dict: dict, operation: str, *args):
        """
        Apply an operation on selected videos from the current view.

        Args:
            selector_dict: {"all": bool, "include": list, "exclude": list}
            operation: "count_property_values" or "edit_property_for_videos"
            *args: Additional arguments for the operation

        Returns:
            Result from the operation (e.g., list of [value, count] pairs)
        """
        if self._provider:
            result = self._provider.apply_on_view(selector_dict, operation, *args)
            self.state_changed.emit()
            return result
        return None

    def close_app(self) -> None:
        """Close the application properly."""
        self._api.close_app()

    # =========================================================================
    # Facade methods — State
    # =========================================================================

    def has_database(self) -> bool:
        """Return whether a database is currently open."""
        return self._database is not None

    def get_database_name(self) -> str:
        """Return the name of the current database."""
        return self._database.get_name() if self._database else ""

    def get_database_folder_path(self) -> str:
        """Return the database folder path as a string."""
        return str(self._database.ways.db_folder) if self._database else ""

    # =========================================================================
    # Facade methods — Application
    # =========================================================================

    def delete_database_by_name(self, name: str) -> None:
        """Delete a database by name from the application registry."""
        self._application.delete_database_from_name(name)
        self.state_changed.emit()

    # =========================================================================
    # Facade methods — Property types
    # =========================================================================

    def get_prop_types(self, **kwargs) -> list[dict]:
        """Return property type definitions."""
        if self._database:
            return self._database.get_prop_types(**kwargs)
        return []

    def create_prop_type(self, name, prop_type, definition, multiple) -> None:
        """Create a new property type."""
        self._database.prop_type_add(name, prop_type, definition, multiple)
        self.state_changed.emit()

    def rename_prop_type(self, name, new_name) -> None:
        """Rename a property type."""
        self._database.prop_type_set_name(name, new_name)
        self.state_changed.emit()

    def delete_prop_type(self, name) -> None:
        """Delete a property type."""
        self._database.prop_type_del(name)
        self.state_changed.emit()

    def set_prop_type_multiple(self, name, multiple) -> None:
        """Set whether a property type allows multiple values."""
        self._database.prop_type_set_multiple(name, multiple)
        self.state_changed.emit()

    # =========================================================================
    # Facade methods — Video entries
    # =========================================================================

    def delete_video_entry(self, video_id) -> None:
        """Delete a video entry from the database."""
        if self._database:
            self._database.video_entry_del(video_id)
            self.state_changed.emit()

    def delete_video_entries(self, video_ids) -> None:
        """Delete multiple video entries from the database."""
        if self._database:
            for video_id in video_ids:
                self._database.video_entry_del(video_id)
            self.state_changed.emit()

    def get_video_by_id(self, video_id) -> VideoPattern | None:
        """Return a single video by ID, or None."""
        if not self._database:
            return None
        videos = self._database.get_videos(where={"video_id": video_id})
        return videos[0] if videos else None

    # =========================================================================
    # Facade methods — Video operations
    # =========================================================================

    def open_video(self, video_id) -> None:
        """Open a video with the default player."""
        if self._ops:
            self._ops.open_video(video_id)

    def rename_video(self, video_id, new_title) -> None:
        """Rename a video file title."""
        if self._ops:
            self._ops.change_video_file_title(video_id, new_title)
            self.state_changed.emit()

    def dismiss_similarity(self, video_id) -> None:
        """Dismiss similarity for a video (mark as no match)."""
        if self._ops:
            self._ops.set_similarities_from_list([video_id], [-1])
            self.state_changed.emit()

    def reset_similarity(self, video_id) -> None:
        """Reset similarity status for a video."""
        if self._ops:
            self._ops.set_similarities_from_list([video_id], [None])
            self.state_changed.emit()

    def mark_as_read(self, video_id) -> None:
        """Toggle the watched/read status of a video."""
        if self._ops:
            self._ops.mark_as_read(video_id)
            self.state_changed.emit()

    def toggle_watched(self, video_id) -> None:
        """Toggle watched status and notify the provider."""
        if self._ops:
            self._ops.mark_as_read(video_id)
            if self._provider:
                self._provider.manage_attributes_modified(
                    ["watched"], is_property=False
                )
            self.state_changed.emit()

    def trash_video(self, video_id) -> None:
        """Move a video file to system trash."""
        if self._ops:
            self._ops.trash_video(video_id)
            self.state_changed.emit()

    def delete_video_file(self, video_id) -> None:
        """Permanently delete a video file."""
        if self._ops:
            self._ops.delete_video(video_id)
            self.state_changed.emit()

    # =========================================================================
    # Facade methods — Provider / view
    # =========================================================================

    def set_group(self, group_id) -> None:
        """Select a group by index."""
        if self._provider:
            self._provider.set_group(group_id)
            self.state_changed.emit()

    def notify_attributes_modified(self, fields, is_property) -> None:
        """Notify the provider that video attributes have been modified."""
        if self._provider:
            self._provider.manage_attributes_modified(fields, is_property=is_property)
            self.state_changed.emit()

    def get_provider_state(self) -> "VideoSearchContext | None":
        """Return the current provider state (minimal, for reading parameters)."""
        if self._provider:
            return self._provider.get_current_state(1, 0)
        return None

    def set_sources(self, sources) -> None:
        """Set the video sources filter."""
        if self._provider:
            self._provider.set_sources(sources)
            self.state_changed.emit()

    def set_groups(
        self, *, field, is_property, sorting, reverse, allow_singletons
    ) -> None:
        """Set the grouping parameters."""
        if self._provider:
            self._provider.set_groups(
                field=field,
                is_property=is_property,
                sorting=sorting,
                reverse=reverse,
                allow_singletons=allow_singletons,
            )
            self.state_changed.emit()

    def clear_groups(self) -> None:
        """Clear (remove) the current grouping."""
        if self._provider:
            self._provider.set_groups(None)
            self.state_changed.emit()

    def set_search(self, text, cond) -> None:
        """Set the search filter."""
        if self._provider:
            self._provider.set_search(text, cond)
            self.state_changed.emit()

    def set_sorting(self, sorting) -> None:
        """Set the sorting order."""
        if self._provider:
            self._provider.set_sort(sorting)
            self.state_changed.emit()

    def get_random_video_id(self) -> int | None:
        """Return a random found video ID."""
        if self._provider:
            return self._provider.get_random_found_video_id()
        return None

    def reset_grouping_and_classifier(self) -> None:
        """Reset grouping, classifier, and group layers to defaults."""
        if self._provider:
            self._provider.reset_parameters(
                self._provider.LAYER_GROUPING,
                self._provider.LAYER_CLASSIFIER,
                self._provider.LAYER_GROUP,
            )
            self.state_changed.emit()

    def set_random_video_search(self, video_id) -> None:
        """Reset grouping/classifier and search for a specific video ID."""
        if self._provider:
            self._provider.reset_parameters(
                self._provider.LAYER_GROUPING,
                self._provider.LAYER_CLASSIFIER,
                self._provider.LAYER_GROUP,
            )
            self._provider.set_search(str(video_id), "id")
            self.state_changed.emit()

    # =========================================================================
    # Facade methods — API
    # =========================================================================

    def playlist(self) -> str:
        """Generate and open a playlist. Returns the filename."""
        return self._api.playlist()

    def open_from_server(self, video_id) -> None:
        """Open a video in VLC via server."""
        self._api.open_from_server(video_id)

    def open_containing_folder(self, video_id) -> None:
        """Open the folder containing a video."""
        self._api.open_containing_folder(video_id)

    # =========================================================================
    # Facade methods — Property values (for dialogs)
    # =========================================================================

    def get_property_values(self, prop_name) -> dict[int, list]:
        """Return all values for a property: {video_id: [values]}."""
        if self._database:
            return self._database.videos_tag_get(prop_name)
        return {}

    def delete_property_values(self, prop_name, values) -> None:
        """Delete specific property values from all videos."""
        if self._algos:
            self._algos.delete_property_values(prop_name, values)
            self.state_changed.emit()

    def replace_property_values(self, prop_name, old_values, new_value) -> bool:
        """Replace property values across all videos. Returns success."""
        if self._algos:
            result = self._algos.replace_property_values(
                prop_name, old_values, new_value
            )
            self.state_changed.emit()
            return result
        return False

    def apply_on_prop_value(self, prop_name, modifier) -> None:
        """Apply a modifier to all values of a property."""
        if self._ops:
            self._ops.apply_on_prop_value(prop_name, modifier)
            self.state_changed.emit()

    def set_video_properties(self, video_id, properties) -> None:
        """Set properties for a single video."""
        if self._database:
            self._database.video_entry_set_tags(video_id, properties)
            self.state_changed.emit()

    # =========================================================================
    # Facade methods — Algorithms
    # =========================================================================

    def move_property_values(self, values, from_name, to_name, *, concatenate) -> int:
        """Move property values between properties. Returns affected video count."""
        if self._algos:
            result = self._algos.move_property_values(
                values, from_name, to_name, concatenate=concatenate
            )
            self.state_changed.emit()
            return result
        return 0

    def fill_property_with_terms(self, prop_name, *, only_empty) -> None:
        """Fill a property with terms extracted from video filenames."""
        if self._algos:
            self._algos.fill_property_with_terms(prop_name, only_empty=only_empty)
            self.state_changed.emit()
