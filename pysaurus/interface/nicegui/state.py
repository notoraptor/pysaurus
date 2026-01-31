"""
Application state management for NiceGUI interface.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Page(str, Enum):
    DATABASES = "databases"
    HOME = "home"
    VIDEOS = "videos"
    PROPERTIES = "properties"


@dataclass
class AppState:
    """Global application state."""

    # Current page
    current_page: Page = Page.DATABASES

    # Database
    database_name: str | None = None
    database_folders: list[str] = field(default_factory=list)

    # Videos page state
    page_size: int = 20
    page_number: int = 0
    selected_videos: set[int] = field(default_factory=set)
    select_all: bool = False

    # Grouping
    group_field: str | None = None
    group_is_property: bool = False
    group_reverse: bool = False
    group_allow_singletons: bool = True
    classifier_path: list[str] = field(default_factory=list)

    # Search
    search_text: str = ""
    search_cond: str = "and"  # and, or, exact, id

    # Sorting
    sorting: list[str] = field(default_factory=list)

    # Sources
    sources: list[list[str]] = field(default_factory=list)

    # Notifications / Progress
    notifications: list[dict[str, Any]] = field(default_factory=list)
    is_loading: bool = False
    progress_message: str = ""
    progress_value: float = 0.0
    progress_total: float = 0.0

    def reset_view(self) -> None:
        """Reset view-related state when changing database."""
        self.page_number = 0
        self.selected_videos.clear()
        self.select_all = False
        self.group_field = None
        self.classifier_path.clear()
        self.search_text = ""
        self.sorting.clear()
        self.sources.clear()

    def clear_notifications(self) -> None:
        """Clear all notifications."""
        self.notifications.clear()

    def add_notification(self, notification: dict[str, Any]) -> None:
        """Add a notification to the list."""
        self.notifications.append(notification)
        # Keep only last 100 notifications
        if len(self.notifications) > 100:
            self.notifications = self.notifications[-100:]


# Global state instance
app_state = AppState()
