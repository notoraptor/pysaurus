"""videre (videroid) application: window, page navigation and backend wiring."""

import logging
from typing import Callable

from videre import Button, Column, Container, Row, Window

from pysaurus.core.notifications import End, Notification
from pysaurus.interface.videroid.context import VideroidContext
from pysaurus.interface.videroid.pages.base_page import Page
from pysaurus.interface.videroid.pages.databases_page import DatabasesPage
from pysaurus.interface.videroid.pages.files_page import FilesPage
from pysaurus.interface.videroid.pages.process_page import ProcessPage
from pysaurus.interface.videroid.pages.properties_page import PropertiesPage
from pysaurus.interface.videroid.pages.videos_page import VideosPage

logger = logging.getLogger(__name__)


class VideroidApp:
    """Top-level controller: owns the window, the pages and the backend bridge."""

    def __init__(self, window: Window | None = None):
        # `window` is injectable for headless tests (e.g. a StepWindow).
        self.window = window or Window(title="Pysaurus", width=1200, height=800)
        self.context = VideroidContext()

        self._pages: dict[str, Page] = {
            "databases": DatabasesPage(self),
            "videos": VideosPage(self),
            "properties": PropertiesPage(self),
            "files": FilesPage(self),
        }
        self._current = "databases"
        # When set, a long operation is running and owns the notifications.
        self._active_process: ProcessPage | None = None

        # Persistent shell: a nav bar (scaffolding until phase 8) and a content
        # holder whose `.control` we swap to navigate — no full rebuild.
        self._content = Container(weight=1)
        self.window.controls = [Column([self._build_nav_bar(), self._content])]

        # Notification bridge (see context.py): api._notify -> window.notify
        # (thread-safe enqueue) -> UI loop -> on_notification (UI thread).
        self.context.set_notification_sink(self.window.notify)
        self.window.add_notification_callback(self.on_notification)

        self.show_page("databases")

    # --- navigation ---------------------------------------------------------

    def show_page(self, name: str) -> None:
        if name not in self._pages:
            raise ValueError(f"Unknown page: {name!r}")
        self._active_process = None
        self._current = name
        page = self._pages[name]
        self._content.control = page.get_widget()
        page.on_show()

    def run_process(
        self, title: str, procedure: Callable[[], None], on_end: Callable[[End], None]
    ) -> None:
        """Show a transient process page, then start a (threaded) backend op.

        Progress notifications are routed to the process page; on the ending
        notification it shows Continue, whose click invokes ``on_end``.
        """

        def finished(end: End) -> None:
            self._active_process = None
            on_end(end)

        self._active_process = ProcessPage(title, finished)
        self._content.control = self._active_process.get_widget()
        # Defer so the process page is shown before the op starts.
        self.window.call_later(procedure)

    def _build_nav_bar(self) -> Row:
        return Row(
            [
                Button(page.title, data=name, on_click=self._on_nav)
                for name, page in self._pages.items()
            ],
            space=4,
        )

    def _on_nav(self, widget) -> None:
        self.show_page(widget.data)

    # --- notifications (UI thread) ------------------------------------------

    def on_notification(self, notification: Notification) -> None:
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
