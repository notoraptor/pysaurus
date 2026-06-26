"""
Application ViewModel for the videre interface.

Mirrors the role of ``pysaurus/interface/pyside6/app_context.py``: it owns the
backend API (:class:`GuiAPI`) and exposes UI-facing actions/accessors. The only
difference with the Qt version is the notification bridge — backend
notifications are routed through videre's notification bus instead of Qt signals.

Extended phase by phase. Phase 0 wires the backend and a few read accessors;
later phases add the action methods (open/create/delete/edit/...).
"""

import logging
from typing import Callable

from pysaurus.core.notifications import Notification
from pysaurus.interface.api.gui_api import GuiAPI

logger = logging.getLogger(__name__)


class _VideroidAPI(GuiAPI):
    """Concrete :class:`GuiAPI` forwarding notifications to a configurable sink.

    ``GuiAPI._notify`` is abstract and is called from ``Information``'s monitor
    thread (a background thread). The sink — set to ``Window.notify`` — re-injects
    the notification into videre's UI loop in a thread-safe way, so the actual UI
    handling happens on the loop thread.
    """

    __slots__ = ("_sink",)

    def __init__(self):
        super().__init__()
        self._sink: Callable[[Notification], None] | None = None

    def set_sink(self, sink: Callable[[Notification], None] | None) -> None:
        self._sink = sink

    def _notify(self, notification: Notification) -> None:
        if self._sink is not None:
            self._sink(notification)


class VideroidContext:
    """Backend façade for the UI: owns the API and exposes actions/accessors."""

    def __init__(self):
        self._api = _VideroidAPI()

    @property
    def api(self) -> _VideroidAPI:
        return self._api

    # --- backend wiring -----------------------------------------------------

    def set_notification_sink(
        self, sink: Callable[[Notification], None] | None
    ) -> None:
        """Route backend notifications to ``sink`` (typically ``Window.notify``)."""
        self._api.set_sink(sink)

    # --- read accessors -----------------------------------------------------

    def has_database(self) -> bool:
        return self._api.database is not None

    def get_database_names(self) -> list[str]:
        return self._api.application.get_database_names()

    def get_database_name(self) -> str:
        db = self._api.database
        return db.get_name() if db is not None else ""

    def get_videos(self, page_size: int, page_number: int, selector=None):
        """Return a VideoSearchContext for the given page (or None if no db)."""
        db = self._api.database
        if db is None:
            return None
        result = db.query_videos(self._api.view, page_size, page_number, selector)
        self._api.view.group = result.group_id
        return result

    # --- actions (long ops are threaded by GuiAPI; they emit DatabaseReady) --

    def open_database(self, name: str, update: bool = False) -> None:
        self._api.open_database(name, update)

    def create_database(
        self, name: str, folders: list[str], update: bool = True
    ) -> None:
        self._api.create_database(name, folders, update)

    def delete_database(self, name: str) -> None:
        self._api.application.delete_database_from_name(name)

    # --- view filters -------------------------------------------------------

    def set_search(self, text: str, cond: str = "and") -> None:
        self._api.set_search(text, cond)

    def set_sorting(self, sorting: list[str]) -> None:
        self._api.set_sorting(sorting)

    def get_prop_types(self, **kwargs):
        db = self._api.database
        return db.get_prop_types(**kwargs) if db is not None else []

    def set_groups(
        self,
        field,
        is_property: bool = False,
        sorting: str = "field",
        reverse: bool = False,
        allow_singletons: bool = True,
    ) -> None:
        self._api.set_groups(field, is_property, sorting, reverse, allow_singletons)

    def clear_groups(self) -> None:
        self._api.set_groups(None)

    def set_group(self, group_id: int) -> None:
        self._api.set_group(group_id)

    def classifier_select_group(self, group_id: int) -> None:
        self._api.classifier_select_group(group_id)

    def classifier_back(self) -> None:
        self._api.classifier_back()

    def classifier_reverse(self) -> None:
        self._api.classifier_reverse()

    def set_sources(self, sources) -> None:
        self._api.set_sources(sources)

    def set_source_expression(self, expression) -> None:
        self._api.view.set_source_expression(expression)

    def get_source_expression(self):
        return self._api.view.source_expression

    # --- video actions ------------------------------------------------------

    @property
    def _ops(self):
        db = self._api.database
        return db.ops if db is not None else None

    def toggle_watched(self, video_id) -> None:
        if self._ops is not None:
            self._ops.mark_as_read(video_id)

    def open_video(self, video_id) -> None:
        if self._ops is not None:
            self._ops.open_video(video_id)

    def open_containing_folder(self, video_id) -> None:
        self._api.open_containing_folder(video_id)

    def rename_video(self, video_id, new_title: str) -> None:
        if self._ops is not None:
            self._ops.change_video_file_title(video_id, new_title)

    def delete_video_entry(self, video_id) -> None:
        db = self._api.database
        if db is not None:
            db.video_entry_del(video_id)

    def trash_video(self, video_id) -> None:
        if self._ops is not None:
            self._ops.trash_video(video_id)

    def delete_video_file(self, video_id) -> None:
        if self._ops is not None:
            self._ops.delete_video(video_id)

    # --- lifecycle ----------------------------------------------------------

    def close_app(self) -> None:
        self._api.close_app()
