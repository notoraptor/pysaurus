"""
Application ViewModel for the videre interface.

Mirrors the role of ``pysaurus/interface/kyuti/app_context.py``: it owns the
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

    def get_all_view_ids(self) -> list:
        """All video ids of the current view (every page), for whole-view
        selection actions. Mirrors how the backend resolves a selector over the
        view: query_videos with page_size=0 returns the whole view (no paging,
        and no view.group side effect — we only want the ids)."""
        db = self._api.database
        if db is None:
            return []
        result = db.query_videos(self._api.view, 0, 0)
        return [video.video_id for video in result.result]

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
        # Mirror kyuti (app_context.set_source_expression): validate the
        # expression before storing it, so an invalid one is rejected up front
        # (raising PysaurusError -> caught by the window's alert hook) instead of
        # being stored silently and crashing every later query_videos.
        db = self._api.database
        if db is None:
            return
        text = expression.strip() if expression else None
        if text:
            from searchexp.errors import ExpressionError

            from pysaurus.application.exceptions import PysaurusError
            from pysaurus.database.saurus.video_mega_group import (
                _compile_source_expression,
            )

            try:
                _compile_source_expression(db.db, text)
            except ExpressionError as exc:
                raise PysaurusError(exc.format_message()) from exc
        self._api.view.set_source_expression(text)

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

    # --- selection / batch actions ------------------------------------------

    def toggle_watched_many(self, video_ids) -> None:
        """Toggle the watched flag on several videos in one batch."""
        if self._ops is not None:
            self._ops.toggle_watched_many(video_ids)

    def delete_video_entries(self, video_ids) -> None:
        """Delete several video entries in a single transaction (files kept)."""
        db = self._api.database
        if db is not None:
            with db.to_save():
                for video_id in video_ids:
                    db.video_entry_del(video_id)

    def call_on_view(self, selector_dict: dict, operation: str, *args):
        """Run a backend ``operation`` on the current view's selected videos.

        ``operation`` is dispatched by the backend (``FeatureAPI.apply_on_view``):
        some operations only read (e.g. ``count_property_values``), others mutate
        (e.g. ``edit_property_for_videos``). After a mutating call the caller must
        reload the page — videroid has no ``state_changed`` signal, so refreshes
        are imperative (unlike the Qt ``app_context``)."""
        if self._api.database is None:
            return None
        return self._api.apply_on_view(selector_dict, operation, *args)

    # --- property types -----------------------------------------------------

    @property
    def _algos(self):
        db = self._api.database
        return db.algos if db is not None else None

    def create_prop_type(self, name, prop_type, definition, multiple) -> None:
        db = self._api.database
        if db is not None:
            db.prop_type_add(name, prop_type, definition, multiple)

    def rename_prop_type(self, name, new_name) -> None:
        db = self._api.database
        if db is not None:
            db.prop_type_set_name(name, new_name)

    def delete_prop_type(self, name) -> None:
        db = self._api.database
        if db is not None:
            db.prop_type_del(name)

    def set_prop_type_multiple(self, name, multiple) -> None:
        db = self._api.database
        if db is not None:
            db.prop_type_set_multiple(name, multiple)

    # --- property values ----------------------------------------------------

    def get_property_values(self, prop_name) -> dict:
        db = self._api.database
        return db.videos_tag_get(prop_name) if db is not None else {}

    def delete_property_values(self, prop_name, values) -> None:
        if self._algos is not None:
            self._algos.delete_property_values(prop_name, values)

    def replace_property_values(self, prop_name, old_values, new_value) -> bool:
        if self._algos is not None:
            return self._algos.replace_property_values(prop_name, old_values, new_value)
        return False

    def move_property_values(self, values, from_name, to_name, *, concatenate) -> int:
        if self._algos is not None:
            return self._algos.move_property_values(
                values, from_name, to_name, concatenate=concatenate
            )
        return 0

    def fill_property_with_terms(self, prop_name, *, only_empty) -> None:
        if self._algos is not None:
            self._algos.fill_property_with_terms(prop_name, only_empty=only_empty)

    def apply_on_prop_value(self, prop_name, modifier) -> None:
        if self._ops is not None:
            self._ops.apply_on_prop_value(prop_name, modifier)

    # --- files (scan / trash) -----------------------------------------------

    def scan_folders(self) -> None:
        """Scan the DB folders for video and non-video files (threaded op)."""
        self._api.scan_folders()

    def get_last_scan_result(self):
        """Return the last FolderScanResult, or None if no scan has run."""
        return self._api.get_last_scan_result()

    def drop_scanned_paths(self, paths) -> None:
        """Remove ``paths`` from the last scan result's "other files".

        Called after trashing files so the Files view reflects the deletion
        without a full rescan. The page used to mutate the FolderScanResult
        directly; centralizing it in the ViewModel keeps that backend-owned
        object out of the page's hands."""
        result = self._api.get_last_scan_result()
        if result is None:
            return
        trashed = set(paths)
        for ext in list(result.others):
            kept = [f for f in result.others[ext] if str(f.path) not in trashed]
            if kept:
                result.others[ext] = kept
            else:
                del result.others[ext]

    def trash_files(self, paths: list) -> tuple[int, list[tuple[str, str]]]:
        """Send files/folders to the system trash → (ok_count, errors).

        Batched send2trash + per-path existence recheck (the batch call gives no
        per-item status). Ported from the Qt app_context."""
        import os

        from send2trash import send2trash

        str_paths = [str(path) for path in paths]
        if not str_paths:
            return 0, []
        catastrophic: str | None = None
        try:
            send2trash(str_paths)
        except OSError:
            pass
        except Exception as exc:
            catastrophic = f"{type(exc).__name__}: {exc}"
        ok = 0
        errors: list[tuple[str, str]] = []
        for path in str_paths:
            if os.path.exists(path):
                errors.append((path, catastrophic or "Failed to send to trash"))
            else:
                ok += 1
        return ok, errors

    # --- database lifecycle -------------------------------------------------

    def update_database(self) -> None:
        """Refresh the current database (threaded op)."""
        self._api.update_database()

    def close_database(self) -> None:
        """Close the current database and reset the view."""
        self._api.close_database()
        self._api.view.reset()

    def rename_database(self, new_name: str) -> None:
        """Rename the current database and update the application registry."""
        db = self._api.database
        if db is None:
            return
        old_path = db.get_database_folder()
        db.rename(new_name)
        new_path = db.get_database_folder()
        application = self._api.application
        if old_path in application.databases:
            del application.databases[old_path]
            application.databases[new_path] = db

    def get_database_folders(self) -> list[str]:
        """Return the database source folders as strings."""
        db = self._api.database
        return [str(folder) for folder in db.get_folders()] if db is not None else []

    def set_database_folders(self, folders: list[str]) -> None:
        """Replace the database source folders."""
        if self._ops is not None:
            self._ops.set_folders(folders)

    # --- lifecycle ----------------------------------------------------------

    def close_app(self) -> None:
        self._api.close_app()
