"""
API Bridge for NiceGUI interface.
Direct Python calls to GuiAPI - no string-based feature lookup.
"""

import logging
from typing import Any, Callable

import pyperclip

from pysaurus.application import exceptions
from pysaurus.core.enumeration import EnumerationError
from pysaurus.core.notifications import Notification
from pysaurus.interface.api.gui_api import GuiAPI
from pysaurus.video.database_context import DatabaseContext

logger = logging.getLogger(__name__)


class NiceGuiAPI(GuiAPI):
    """GuiAPI subclass for NiceGUI with notification handling."""

    __slots__ = ("_notification_handlers",)

    def __init__(self):
        super().__init__()
        self._notification_handlers: list[Callable[[dict[str, Any]], None]] = []

    def _notify(self, notification: Notification) -> None:
        """Handle notifications from the backend."""
        nt = notification.describe()
        logger.debug(f"Notification: {nt.get('name', 'unknown')}")
        for handler in self._notification_handlers:
            try:
                handler(nt)
            except Exception as e:
                logger.exception(f"Error in notification handler: {e}")

    def add_notification_handler(
        self, handler: Callable[[dict[str, Any]], None]
    ) -> None:
        """Register a notification handler."""
        self._notification_handlers.append(handler)

    def remove_notification_handler(
        self, handler: Callable[[dict[str, Any]], None]
    ) -> None:
        """Unregister a notification handler."""
        if handler in self._notification_handlers:
            self._notification_handlers.remove(handler)


def _wrap_error(func):
    """Decorator to wrap exceptions into error dict."""

    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return {"error": False, "data": result}
        except (OSError, EnumerationError, exceptions.PysaurusError) as exc:
            logger.exception(f"API call error: {func.__name__}")
            return {
                "error": True,
                "data": {"name": type(exc).__name__, "message": str(exc)},
            }

    return wrapper


class APIBridge:
    """
    Bridge between NiceGUI interface and GuiAPI.
    Uses direct Python calls instead of string-based feature lookup.
    """

    __slots__ = ("_api",)

    def __init__(self):
        self._api: NiceGuiAPI | None = None

    @property
    def api(self) -> NiceGuiAPI:
        """Lazy initialization of API."""
        if self._api is None:
            self._api = NiceGuiAPI()
        return self._api

    # -------------------------------------------------------------------------
    # Database operations
    # -------------------------------------------------------------------------

    def get_database_names(self) -> list[str]:
        """Get list of available database names."""
        return self.api.application.get_database_names() or []

    @_wrap_error
    def create_database(self, name: str, folders: list[str], update: bool = True):
        """Create a new database."""
        return self.api.create_database(name, folders, update)

    @_wrap_error
    def open_database(self, name: str, update: bool = True):
        """Open an existing database."""
        return self.api.open_database(name, update)

    @_wrap_error
    def delete_database(self):
        """Delete the current database."""
        return self.api.delete_database()

    @_wrap_error
    def rename_database(self, new_name: str):
        """Rename the current database."""
        return self.api.database.rename(new_name)

    @_wrap_error
    def close_database(self):
        """Close the current database."""
        return self.api.close_database()

    @_wrap_error
    def update_database(self):
        """Refresh/scan the current database."""
        return self.api.update_database()

    # -------------------------------------------------------------------------
    # Backend state
    # -------------------------------------------------------------------------

    def get_constants(self) -> dict[str, Any]:
        """Get backend constants."""
        return self.api.get_constants()

    def get_python_backend(
        self, page_size: int, page_number: int, selector: dict | None = None
    ) -> DatabaseContext:
        """Get current backend state as Python object."""
        return self.api.get_python_backend(page_size, page_number, selector)

    def backend(
        self, page_size: int, page_number: int, selector: dict | None = None
    ) -> dict[str, Any]:
        """Get current backend state with videos as dict."""
        return self.get_python_backend(page_size, page_number, selector).json()

    # -------------------------------------------------------------------------
    # Property types
    # -------------------------------------------------------------------------

    def describe_prop_types(self) -> list[dict[str, Any]]:
        """Get list of property type definitions."""
        return self.api.database.get_prop_types() if self.api.database else []

    @_wrap_error
    def create_prop_type(
        self, name: str, prop_type: str, definition: Any = None, multiple: bool = False
    ):
        """Create a new property type."""
        return self.api.database.prop_type_add(name, prop_type, definition, multiple)

    @_wrap_error
    def remove_prop_type(self, name: str):
        """Remove a property type."""
        return self.api.database.prop_type_del(name)

    @_wrap_error
    def rename_prop_type(self, old_name: str, new_name: str):
        """Rename a property type."""
        return self.api.database.prop_type_set_name(old_name, new_name)

    @_wrap_error
    def convert_prop_multiplicity(self, name: str, multiple: bool):
        """Convert property between unique and multiple."""
        return self.api.database.prop_type_set_multiple(name, multiple)

    # -------------------------------------------------------------------------
    # Video operations
    # -------------------------------------------------------------------------

    @_wrap_error
    def open_video(self, video_id: int):
        """Open a video file."""
        return self.api.database.ops.open_video(video_id)

    @_wrap_error
    def open_random_video(self):
        """Open a random video."""
        return self.api.database.provider.choose_random_video()

    @_wrap_error
    def open_from_server(self, video_id: int):
        """Open video from internal server (VLC)."""
        return self.api.open_from_server(video_id)

    @_wrap_error
    def mark_as_read(self, video_id: int):
        """Toggle video as read/unread."""
        return self.api.database.ops.mark_as_read(video_id)

    @_wrap_error
    def delete_video(self, video_id: int):
        """Delete video file and entry."""
        return self.api.database.ops.delete_video(video_id)

    @_wrap_error
    def delete_video_entry(self, video_id: int):
        """Delete video entry only (keep file)."""
        return self.api.database.video_entry_del(video_id)

    @_wrap_error
    def rename_video(self, video_id: int, new_title: str):
        """Rename video file."""
        return self.api.database.ops.change_video_file_title(video_id, new_title)

    @_wrap_error
    def move_video_file(self, video_id: int, directory: str):
        """Move video file to another directory."""
        return self.api.move_video_file(video_id, directory)

    @_wrap_error
    def set_video_properties(self, video_id: int, properties: dict[str, Any]):
        """Set properties for a video."""
        return self.api.database.video_entry_set_tags(video_id, properties)

    # -------------------------------------------------------------------------
    # View operations
    # -------------------------------------------------------------------------

    @_wrap_error
    def set_sources(self, paths: list[list[str]]):
        """Set source paths filter."""
        return self.api.database.provider.set_sources(paths)

    @_wrap_error
    def set_groups(
        self,
        field: str,
        is_property: bool = False,
        sorting: str = "field",
        reverse: bool = False,
        allow_singletons: bool = True,
    ):
        """Set grouping configuration."""
        return self.api.database.provider.set_groups(
            field, is_property, sorting, reverse, allow_singletons
        )

    @_wrap_error
    def set_search(self, text: str, cond: str = "and"):
        """Set search filter."""
        return self.api.database.provider.set_search(text, cond)

    @_wrap_error
    def set_sorting(self, sorting: list[str]):
        """Set sorting configuration."""
        return self.api.database.provider.set_sort(sorting)

    @_wrap_error
    def classifier_select_group(self, group_id: int):
        """Select a group in classifier mode."""
        return self.api.database.provider.classifier_select_group(group_id)

    @_wrap_error
    def classifier_back(self):
        """Go back in classifier path."""
        return self.api.database.provider.classifier_back()

    @_wrap_error
    def classifier_reverse(self):
        """Reverse classifier path."""
        return self.api.database.provider.classifier_reverse()

    # -------------------------------------------------------------------------
    # Batch operations
    # -------------------------------------------------------------------------

    @_wrap_error
    def apply_on_view(self, selector: dict, fn_name: str, *fn_args):
        """Apply a function on selected videos."""
        return self.api.database.provider.apply_on_view(selector, fn_name, *fn_args)

    @_wrap_error
    def find_similar_videos(self):
        """Find similar videos in database."""
        return self.api.find_similar_videos()

    # -------------------------------------------------------------------------
    # Utility operations
    # -------------------------------------------------------------------------

    @_wrap_error
    def clipboard(self, text: str):
        """Copy text to clipboard."""
        return pyperclip.copy(text)

    def select_directory(self) -> str | None:
        """Open directory selection dialog."""
        import filedial

        return filedial.select_directory()

    def select_file(self) -> str | None:
        """Open file selection dialog."""
        import filedial

        return filedial.select_file_to_open()

    @_wrap_error
    def open_containing_folder(self, video_id: int):
        """Open folder containing video."""
        return self.api.open_containing_folder(video_id)

    def playlist(self) -> str:
        """Create and open playlist."""
        return self.api.playlist()

    @_wrap_error
    def cancel_copy(self):
        """Cancel ongoing copy operation."""
        return self.api.cancel_copy()

    def close_app(self):
        """Close the application."""
        if self._api:
            self._api.close_app()

    # -------------------------------------------------------------------------
    # Notification handling
    # -------------------------------------------------------------------------

    def add_notification_handler(
        self, handler: Callable[[dict[str, Any]], None]
    ) -> None:
        """Register a notification handler."""
        self.api.add_notification_handler(handler)

    def remove_notification_handler(
        self, handler: Callable[[dict[str, Any]], None]
    ) -> None:
        """Unregister a notification handler."""
        self.api.remove_notification_handler(handler)


# Global API bridge instance
api_bridge = APIBridge()
