"""videre (videroid) application: window, app shell (title / menu bar / status
bar / page selector) and backend wiring."""

import logging
from datetime import datetime
from typing import Callable

import videre
from videre import Window

from pysaurus.core.core_exceptions import ApplicationError
from pysaurus.interface.videroid.context import VideroidContext
from pysaurus.interface.videroid.dialogs.edit_folders_dialog import EditFoldersDialog
from pysaurus.interface.videroid.pages.base_page import Page
from pysaurus.interface.videroid.pages.databases_page import DatabasesPage
from pysaurus.interface.videroid.pages.files_page import FilesPage
from pysaurus.interface.videroid.pages.process_page import ProcessPage
from pysaurus.interface.videroid.pages.properties_page import PropertiesPage
from pysaurus.interface.videroid.pages.videos_page import VideosPage

logger = logging.getLogger(__name__)

_PAGE_SIZES = (10, 20, 50, 100)
# videre gap G-TITLE: Window.title has no setter → the dynamic title is an
# in-app label (the OS caption stays "Pysaurus"). G3: the menu bar is composed
# from ContextButtons (one flat menu each) rather than a native MenuBar.

# Status bar: a passive strip (kyuti's QStatusBar). A Div is used only so a click
# can CLEAR the message (kyuti clearMessage); every state (default/hover/click)
# shares the same look, so it never highlights or reads as a button (unlike a
# plain Div, whose default is a centered, bordered, hover-highlighting box).
_STATUS_STYLE = {
    _state: {
        "background_color": "#f0f0f0",
        "border": videre.Border(top=(1, videre.Colors.lightgray)),
        "horizontal_alignment": videre.Alignment.START,
        "padding": videre.Padding.axis(horizontal=6, vertical=4),
    }
    for _state in ("default", "hover", "click")
}


class VideroidApp:
    """Top-level controller: owns the window, the pages and the app shell."""

    def __init__(self, window: Window | None = None):
        # `window` is injectable for headless tests (e.g. a StepWindow).
        # Warning vs fatal split (kyuti main.py PySide6ExceptHook): expected
        # application/OS errors -> non-fatal alert dialog; anything else is a
        # bug -> videre stops the loop cleanly and Window.run() re-raises, so
        # the traceback reaches the console and the process exits non-zero.
        # (kyuti also shows the traceback in a "Fatal Error" dialog before
        # exiting — videre's lifecycle cannot show-then-exit.)
        # dpi_aware (videre phase 1 of G-DPI): on a scaled display (e.g. 150%)
        # the window opens at device-pixel size and text is rasterized at
        # native resolution — sharp instead of bitmap-stretched by the OS.
        self.window = window or Window(
            title="Pysaurus",
            width=1200,
            height=800,
            alert_on_exceptions=(ApplicationError, OSError),
            dpi_aware=True,
        )
        self.context = VideroidContext()

        self._pages: dict[str, Page] = {
            "databases": DatabasesPage(self),
            "videos": VideosPage(self),
            "properties": PropertiesPage(self),
            "files": FilesPage(self),
        }
        # Typed handle for the videos page: it exposes page-size/deletion-
        # confirmation state and a refresh() the shell menu/actions need,
        # which the generic Page base class doesn't declare.
        self._videos_page: VideosPage = self._pages["videos"]
        self._current = "databases"
        self._active_process: ProcessPage | None = None
        self._process_title = ""
        # Session log (kyuti): every status message is timestamped, kept in
        # memory, and appended to <db folder>/session_log.txt while a database
        # is open (the session header is flushed once per database).
        self._session_log: list[str] = []
        self._log_file_initialized: set[str] = set()
        self._log_session_start()

        # Shell widgets (persistent; rebuilt in place on navigation/state).
        self._title_label = videre.Text("Pysaurus", strong=True)
        self._status = videre.Text("Ready")
        self._menu_holder = videre.Container()
        self._content = videre.Container(weight=1)
        self.window.controls = [
            videre.Column(
                [
                    videre.Container(
                        self._title_label,
                        padding=videre.Padding.axis(vertical=2, horizontal=6),
                    ),
                    self._menu_holder,
                    self._content,
                    # Status bar: passive-looking strip that clears on click
                    # (kyuti). _STATUS_STYLE neutralizes the Div button chrome.
                    videre.Div(
                        self._status,
                        style=_STATUS_STYLE,
                        on_click=lambda w: self._set_status(""),
                    ),
                ],
                space=0,
            )
        ]

        # Notification bridge (see context.py): api._notify -> window.notify
        # (thread-safe) -> UI loop -> on_notification (UI thread).
        self.context.set_notification_sink(self.window.notify)
        self.window.add_notification_callback(self.on_notification)
        # Surface background-op failures instead of a silent "success" (kyuti).
        self.context.set_exception_sink(self._on_thread_exception)

        self.show_page("databases")

    # --- navigation ---------------------------------------------------------

    def show_page(self, name: str) -> None:
        if name not in self._pages:
            raise ValueError(f"Unknown page: {name!r}")
        # Videos/Properties/Files need an open database; fall back otherwise.
        if name != "databases" and not self.context.has_database():
            name = "databases"
        self._active_process = None
        self._current = name
        page = self._pages[name]
        self._content.control = page.get_widget()
        page.on_show()
        self._refresh_shell()

    def run_process(self, title, procedure, on_end, autocontinue=False) -> None:
        """Show a transient process page, then start a (threaded) backend op."""

        def finished(end) -> None:
            self._active_process = None
            on_end(end)
            self._refresh_shell()

        self._process_title = title
        self._active_process = ProcessPage(title, finished, autocontinue=autocontinue)
        self._content.control = self._active_process.get_widget()
        self._refresh_shell()
        # Defer so the process page is shown before the op starts.
        self.window.call_later(procedure)

    def _on_nav(self, widget) -> None:
        self.show_page(widget.data)

    # --- shell --------------------------------------------------------------

    def _set_status(self, message: str) -> None:
        self._status.text = message
        # Every status message lands in the session log (kyuti logs the
        # page-emitted ones; here _set_status is the single funnel). Clearing
        # the bar (empty message, e.g. the click-to-clear) is not logged.
        if message:
            self._log_message(message)

    # --- session log ----------------------------------------------------------

    def _log_session_start(self) -> None:
        started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._session_log += ["=" * 60, f"Session started: {started}", "=" * 60]

    def _log_message(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self._session_log.append(entry)
        self._save_log_to_file(entry)

    def _save_log_to_file(self, entry: str) -> None:
        # Append to session_log.txt in the open database's folder. On the first
        # write for a database, flush everything logged so far this session
        # (header + any pre-open messages) before the entry (kyuti).
        if not self.context.has_database():
            return
        log_file = f"{self.context.get_database_folder_path()}/session_log.txt"
        db_name = self.context.get_database_name()
        if db_name not in self._log_file_initialized:
            with open(log_file, "a", encoding="utf-8") as file:
                file.write("\n")
                for line in self._session_log[:-1]:
                    file.write(line + "\n")
            self._log_file_initialized.add(db_name)
        with open(log_file, "a", encoding="utf-8") as file:
            file.write(entry + "\n")

    def _show_session_log(self) -> None:
        # Read-only view of the in-memory log, scrolled to the end (kyuti's
        # SessionLogDialog; monospace = videre gap G17).
        self.window.set_fancybox(
            videre.Container(
                videre.ScrollView(
                    videre.Text(
                        "\n".join(self._session_log), wrap=videre.TextWrap.WORD
                    ),
                    wrap_horizontal=True,
                    default_bottom=True,
                ),
                height=400,
                padding=videre.Padding.all(6),
            ),
            title="Session Log",
            buttons=[videre.FancyCloseButton("Close")],
        )

    def _refresh_shell(self) -> None:
        has_db = self.context.has_database() and self._active_process is None
        on_videos = self._current == "videos"
        menus = [
            # Database menu stays enabled even without a DB so Quit is always
            # reachable (kyuti keeps Quit active). videre can't grey individual
            # flat-menu items (G10), so without a DB we show only Quit.
            videre.ContextButton("Database", actions=self._menu_database(has_db)),
            videre.ContextButton(
                "View", actions=self._menu_view(), disabled=not (has_db and on_videos)
            ),
            videre.ContextButton(
                "Options", actions=self._menu_options(), disabled=not has_db
            ),
            videre.ContextButton("Help", actions=self._menu_help()),
        ]
        right = []
        if has_db:
            for name, label in (
                ("videos", "Videos"),
                ("properties", "Properties"),
                ("files", "Files"),
            ):
                mark = "● " if self._current == name else "○ "
                right.append(
                    videre.Button(mark + label, data=name, on_click=self._on_nav)
                )
        self._menu_holder.control = videre.Row(
            [*menus, videre.Container(weight=1), *right],
            space=6,
            vertical_alignment=videre.Alignment.CENTER,
        )
        self._title_label.text = self._compute_title()

    def _compute_title(self) -> str:
        if self._active_process is not None:
            return f"Pysaurus - {self._process_title}"
        db = self.context.get_database_name()
        if self._current == "databases" or not db:
            return "Pysaurus - Databases"
        if self._current == "videos":
            return f"Pysaurus - {db}"
        return f"Pysaurus - {self._current.capitalize()} - {db}"

    # --- menus --------------------------------------------------------------

    def _menu_database(self, has_db: bool = True):
        # Quit is always available (kyuti). Order mirrors kyuti (Rename, Edit,
        # Update, Find Similar/Re-encoded, Close, Quit); Session Log is a
        # deferred feature (not yet ported).
        if not has_db:
            return [("Quit", self._quit)]
        return [
            ("Rename Database…", self._rename_db),
            ("Edit Folders…", self._edit_folders),
            ("Update Database", self._update_db),
            ("Find Similar Videos", self._find_similar),
            ("Find Re-encoded Videos", self._find_reencoded),
            ("Close Database", self._close_db),
            ("Session Log...", self._show_session_log),
            ("Quit", self._quit),
        ]

    def _menu_view(self):
        return [
            ("Random Video", self._random_video),
            ("Generate Playlist", self._generate_playlist),
            ("Refresh View", self._refresh_view),
        ]

    def _menu_options(self):
        page_size = self._videos_page.page_size
        actions: list[tuple[str, Callable[..., None]]] = [
            (
                f"{'● ' if page_size == size else '○ '}Page size {size}",
                lambda s=size: self._set_page_size(s),
            )
            for size in _PAGE_SIZES
        ]
        mark = "☑ " if self._videos_page.confirm_not_found_deletion else "☐ "
        actions.append(
            (f"{mark}Confirm deletion of missing entries", self._toggle_confirm_del)
        )
        return actions

    def _menu_help(self):
        return [("About", self._about)]

    # --- menu actions -------------------------------------------------------

    def _update_db(self) -> None:
        self.run_process(
            "Updating database",
            self.context.update_database,
            self._on_videos_operation_end_reset_selection,
        )

    def _find_similar(self) -> None:
        self.window.confirm(
            "Search for visually similar videos? This may take a while.",
            "Find Similar Videos",
            on_confirm=lambda: self.run_process(
                "Finding similar videos",
                self.context.find_similar_videos,
                self._on_videos_operation_end_reset_selection,
            ),
        )

    def _find_reencoded(self) -> None:
        self.window.confirm(
            "Search for potentially re-encoded videos? This may take a while.",
            "Find Re-encoded Videos",
            on_confirm=lambda: self.run_process(
                "Finding re-encoded videos",
                self.context.find_similar_videos_reencoded,
                self._on_videos_operation_end_reset_selection,
            ),
        )

    def _on_videos_operation_end_reset_selection(self, end) -> None:
        """Handle completion of an operation that changes the video set
        (update, find similar/re-encoded), clearing the now possibly-stale
        selection."""
        self._videos_page._clear_selection()
        self.show_page("videos")

    def _rename_db(self) -> None:
        entry = videre.TextInput(self.context.get_database_name())
        self.window.set_fancybox(
            videre.Column([videre.Text("Rename database to:"), entry], space=8),
            title="Rename Database",
            buttons=[
                videre.FancyCloseButton(
                    "Rename", on_click=lambda w: self._do_rename_db(entry)
                ),
                videre.FancyCloseButton("Cancel"),
            ],
        )

    def _do_rename_db(self, entry) -> None:
        new_name = entry.value.strip()
        if new_name and new_name != self.context.get_database_name():
            self.context.rename_database(new_name)
            self._refresh_shell()
            self._set_status(f"Database renamed to '{new_name}'.")

    def _edit_folders(self) -> None:
        dialog = EditFoldersDialog(self.context.get_database_folders())
        self.window.set_fancybox(
            dialog,
            title="Edit Folders",
            buttons=[
                videre.FancyCloseButton(
                    "Apply", on_click=lambda w: self._do_edit_folders(dialog)
                ),
                videre.FancyCloseButton("Cancel"),
            ],
        )

    def _do_edit_folders(self, dialog) -> None:
        folders = dialog.get_folders()
        if set(folders) != set(self.context.get_database_folders()):
            self.context.set_database_folders(folders)
            self._set_status(
                "Folders updated — use Database ▸ Update Database to rescan."
            )

    def _close_db(self) -> None:
        self.window.confirm(
            "Close the current database?",
            "Close Database",
            on_confirm=self._do_close_db,
        )

    def _do_close_db(self) -> None:
        self.context.close_database()
        self.show_page("databases")
        self._set_status("Database closed.")

    def _quit(self) -> None:
        self.window.confirm(
            "Are you sure you want to quit?", "Quit", on_confirm=self._do_quit
        )

    def _do_quit(self) -> None:
        self.context.close_app()
        # Ask the event loop to exit; run()'s `finally` then calls the windowing's
        # stop() (pygame.quit()) ONCE, after the frame. Tearing pygame down here
        # mid-step would crash the rest of the current _step ("video system not
        # initialized"), so we only request the stop and let run() do the teardown.
        self.window.stop()

    def _refresh_view(self) -> None:
        self._videos_page.refresh()
        self._set_status("View refreshed.")

    def _random_video(self) -> None:
        # Opens a random unwatched video and narrows the view to it (kyuti).
        self.context.open_random_video()
        self._videos_page.refresh()

    def _generate_playlist(self) -> None:
        path = self.context.generate_playlist()
        self._set_status(f"Playlist created: {path}")

    def _on_thread_exception(self, exception) -> None:
        # A background @process op (open/update/scan) failed. Runs on a worker
        # thread: call_later marshals a re-raise onto the UI loop, where the
        # task wrapper applies the same warning/fatal split as event handlers
        # (kyuti re-raises in the main thread for its excepthook the same way).
        def reraise():
            raise exception

        self.window.call_later(reraise)

    def _set_page_size(self, size: int) -> None:
        videos = self._videos_page
        videos.page_size = size  # setter resets to page 0 and reloads
        self._refresh_shell()
        self._set_status(f"Page size: {size}.")

    def _toggle_confirm_del(self) -> None:
        videos = self._videos_page
        videos.confirm_not_found_deletion = not videos.confirm_not_found_deletion
        self._refresh_shell()

    def _about(self) -> None:
        # Two lines, mirroring kyuti's About (main_window.py:461-463).
        self.window.alert(
            "Pysaurus - Video Collection Manager\n\n"
            "A desktop interface for managing video collections (videre).",
            "About",
        )

    # --- notifications (UI thread) ------------------------------------------

    def on_notification(self, notification) -> None:
        logger.debug("Notification: %s", type(notification).__name__)
        if self._active_process is not None:
            self._active_process.on_notification(notification)
        else:
            self._pages[self._current].on_notification(notification)

    # --- lifecycle ----------------------------------------------------------

    def run(self) -> int:
        try:
            return self.window.run()
        finally:
            self.context.close_app()
