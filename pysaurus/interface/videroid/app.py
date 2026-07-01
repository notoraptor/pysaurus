"""videre (videroid) application: window, app shell (title / menu bar / status
bar / page selector) and backend wiring."""

import logging

import videre
from videre import Window

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


class VideroidApp:
    """Top-level controller: owns the window, the pages and the app shell."""

    def __init__(self, window: Window | None = None):
        # `window` is injectable for headless tests (e.g. a StepWindow).
        # alert_on_exceptions (phase 8.3): videre shows an error dialog instead of
        # crashing on a handled exception in an event handler.
        self.window = window or Window(
            title="Pysaurus", width=1200, height=800, alert_on_exceptions=(Exception,)
        )
        self.context = VideroidContext()

        self._pages: dict[str, Page] = {
            "databases": DatabasesPage(self),
            "videos": VideosPage(self),
            "properties": PropertiesPage(self),
            "files": FilesPage(self),
        }
        self._current = "databases"
        self._active_process: ProcessPage | None = None
        self._process_title = ""

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
                    # Status bar: a passive strip (like kyuti's QStatusBar), NOT a
                    # button. A `Div` here would render as a bordered, centered,
                    # hover-highlighting box — indistinguishable from a button.
                    videre.Container(
                        self._status,
                        background_color="#f0f0f0",
                        border=videre.Border(top=(1, videre.Colors.lightgray)),
                        padding=videre.Padding.axis(horizontal=6, vertical=4),
                        horizontal_alignment=videre.Alignment.START,
                    ),
                ],
                space=0,
            )
        ]

        # Notification bridge (see context.py): api._notify -> window.notify
        # (thread-safe) -> UI loop -> on_notification (UI thread).
        self.context.set_notification_sink(self.window.notify)
        self.window.add_notification_callback(self.on_notification)

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

    def run_process(self, title, procedure, on_end) -> None:
        """Show a transient process page, then start a (threaded) backend op."""

        def finished(end) -> None:
            self._active_process = None
            on_end(end)
            self._refresh_shell()

        self._process_title = title
        self._active_process = ProcessPage(title, finished)
        self._content.control = self._active_process.get_widget()
        self._refresh_shell()
        # Defer so the process page is shown before the op starts.
        self.window.call_later(procedure)

    def _on_nav(self, widget) -> None:
        self.show_page(widget.data)

    # --- shell --------------------------------------------------------------

    def _set_status(self, message: str) -> None:
        self._status.text = message

    def _refresh_shell(self) -> None:
        has_db = self.context.has_database() and self._active_process is None
        on_videos = self._current == "videos"
        menus = [
            videre.ContextButton(
                "Database", actions=self._menu_database(), disabled=not has_db
            ),
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

    def _menu_database(self):
        return [
            ("Update Database", self._update_db),
            ("Rename Database…", self._rename_db),
            ("Edit Folders…", self._edit_folders),
            ("Close Database", self._close_db),
            ("Quit", self._quit),
        ]

    def _menu_view(self):
        return [("Refresh View", self._refresh_view)]

    def _menu_options(self):
        page_size = self._pages["videos"].page_size
        actions = [
            (
                f"{'● ' if page_size == size else '○ '}Page size {size}",
                lambda s=size: self._set_page_size(s),
            )
            for size in _PAGE_SIZES
        ]
        mark = "☑ " if self._pages["videos"].confirm_not_found_deletion else "☐ "
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
            lambda end: self.show_page("videos"),
        )

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
        self.window.windowing.stop()

    def _refresh_view(self) -> None:
        self._pages["videos"].refresh()
        self._set_status("View refreshed.")

    def _set_page_size(self, size: int) -> None:
        videos = self._pages["videos"]
        videos.page_size = size  # setter resets to page 0 and reloads
        self._refresh_shell()
        self._set_status(f"Page size: {size}.")

    def _toggle_confirm_del(self) -> None:
        videos = self._pages["videos"]
        videos.confirm_not_found_deletion = not videos.confirm_not_found_deletion
        self._refresh_shell()

    def _about(self) -> None:
        self.window.alert(
            "Pysaurus — Video Collection Manager (videre interface).", "About"
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
