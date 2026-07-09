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
import os
from typing import TYPE_CHECKING, Callable, cast

from searchexp.errors import ExpressionError

from pysaurus.application.exceptions import PysaurusError
from pysaurus.core.notifications import Notification
from pysaurus.database.algorithms.folder_scan import FolderScanResult
from pysaurus.database.saurus.video_mega_group import _compile_source_expression
from pysaurus.interface.api.gui_api import GuiAPI

if TYPE_CHECKING:
    from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection

logger = logging.getLogger(__name__)


class _VideroidAPI(GuiAPI):
    """Concrete :class:`GuiAPI` forwarding notifications to a configurable sink.

    ``GuiAPI._notify`` is abstract and is called from ``Information``'s monitor
    thread (a background thread). The sink — set to ``Window.notify`` — re-injects
    the notification into videre's UI loop in a thread-safe way, so the actual UI
    handling happens on the loop thread.
    """

    __slots__ = ("_sink", "_exception_callback")

    def __init__(self):
        super().__init__()
        self._sink: Callable[[Notification], None] | None = None
        self._exception_callback: Callable[[Exception], None] | None = None

    def set_sink(self, sink: Callable[[Notification], None] | None) -> None:
        self._sink = sink

    def set_exception_callback(
        self, callback: Callable[[Exception], None] | None
    ) -> None:
        self._exception_callback = callback

    def _notify(self, notification: Notification) -> None:
        if self._sink is not None:
            self._sink(notification)

    def _run_thread(self, function, *args, **kwargs):
        # Catch exceptions raised by background @process ops (open/update/scan)
        # and route them to the UI instead of losing them to stderr — otherwise
        # a failed op shows a "success" in the ProcessPage. Mirrors
        # KyutiAPI._run_thread (kyuti_api.py:50-60).
        def wrapper():
            try:
                function(*args, **kwargs)
            except Exception as exc:
                if self._exception_callback is not None:
                    self._exception_callback(exc)

        return super()._run_thread(wrapper)


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

    def set_exception_sink(self, callback: Callable[[Exception], None] | None) -> None:
        """Route background-thread op exceptions to ``callback``. Fires on a
        worker thread — the caller must reach the UI thread-safely."""
        self._api.set_exception_callback(callback)

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

    def get_view_generation(self) -> int:
        """Return the view's generation counter (bumped by any filter change:
        sources, search, grouping, group, classifier — not sorting). Interfaces
        use this to detect when a cross-page video selection is stale."""
        return self._api.view.generation

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

    def focus_prop_val(self, prop_name, field_value) -> None:
        self._api.focus_prop_val(prop_name, field_value)

    def classifier_concatenate_path(self, to_property) -> None:
        """Concatenate the classifier path into a single string property."""
        self._api.classifier_concatenate_path(to_property)

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
            try:
                _compile_source_expression(cast("PysaurusCollection", db).db, text)
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

    def open_from_server(self, video_id) -> str:
        """Open a video via the server (VLC). Returns the server path/URL."""
        return self._api.open_from_server(video_id)

    def open_random_video(self) -> None:
        """Pick a random unwatched video, open it, and narrow the view to it."""
        self._api.open_random_video()

    def generate_playlist(self) -> str:
        """Build (and open) an XSPF playlist of the current view; return its path."""
        return self._api.playlist()

    def find_similar_videos(self) -> None:
        """Search for visually similar videos (threaded @process); groups by id."""
        self._api.find_similar_videos()

    def find_similar_videos_reencoded(self) -> None:
        """Search for re-encoded videos (threaded @process); groups by re-enc id."""
        self._api.find_similar_videos_reencoded()

    def dismiss_similarity(self, video_id, field="similarity_id") -> None:
        """Mark a video as having no similar match (-1)."""
        if self._ops is not None:
            self._ops.set_similarities_from_list([video_id], [-1], field=field)

    def reset_similarity(self, video_id, field="similarity_id") -> None:
        """Reset a video's similarity so it is re-evaluated next search (None)."""
        if self._ops is not None:
            self._ops.set_similarities_from_list([video_id], [None], field=field)

    def confirm_move(self, src_video_id, dst_video_id) -> None:
        """Transfer a missing video's metadata onto its found destination entry
        and delete the missing entry (synchronous)."""
        if self._ops is not None:
            self._ops.move_video_entry(src_video_id, dst_video_id)

    def confirm_unique_moves(self) -> int:
        """Confirm every move with exactly one destination; returns the count."""
        if self._algos is not None:
            return self._algos.confirm_unique_moves()
        return 0

    def set_video_properties(self, video_id, properties: dict) -> None:
        """Replace properties on one video ({name: [values]}; an empty list
        deletes the property from the video). Synchronous."""
        db = self._api.database
        if db is not None:
            db.video_entry_set_tags(video_id, properties)

    def add_property_value_for_videos(self, video_ids, prop_name, values) -> None:
        """Set `values` on a property for several videos — merged with existing
        values if the property is multiple, replacing them otherwise."""
        db = self._api.database
        if db is not None and self._ops is not None:
            (prop,) = db.get_prop_types(name=prop_name)
            self._ops.set_property_for_videos(
                prop_name, {vid: values for vid in video_ids}, merge=prop.multiple
            )

    def open_containing_folder(self, video_id) -> None:
        self._api.open_containing_folder(video_id)

    def move_video_file(self, video_id, directory) -> None:
        """Move a video's file to `directory` (threaded @process; the dir must be
        inside a DB folder or the op notifies an error). Emits Done/Cancelled/End."""
        self._api.move_video_file(video_id, directory)

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

    def get_last_scan_result(self) -> FolderScanResult | None:
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
        # Local import: tests monkeypatch "send2trash.send2trash" directly, which
        # only takes effect if this name is looked up fresh on each call.
        from send2trash import send2trash  # noqa: PLC0415

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

    def get_database_folder_path(self) -> str:
        """The open database's own folder (where session_log.txt lives), or ""."""
        db = self._api.database
        return str(db.get_database_folder()) if db is not None else ""

    def set_database_folders(self, folders: list[str]) -> None:
        """Replace the database source folders."""
        if self._ops is not None:
            self._ops.set_folders(folders)

    # --- lifecycle ----------------------------------------------------------

    def close_app(self) -> None:
        self._api.close_app()
