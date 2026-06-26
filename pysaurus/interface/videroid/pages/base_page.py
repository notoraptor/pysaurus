"""Base class shared by all videroid pages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from videre import Text
from videre.widgets.widget import Widget

if TYPE_CHECKING:
    from pysaurus.core.notifications import Notification
    from pysaurus.interface.videroid.app import VideroidApp
    from pysaurus.interface.videroid.context import VideroidContext


class Page:
    """A single application screen.

    The widget tree is built once (lazily, cached) and reused across
    navigations; pages refresh by mutating their sub-widgets in place (e.g.
    ``column.controls = [...]``), not by rebuilding the whole tree — this is the
    videre idiom and it preserves widget state (text inputs, etc.).
    """

    #: Label shown in the navigation bar (and, later, the window title).
    title: str = "Page"

    def __init__(self, app: VideroidApp):
        self.app = app
        self.context: VideroidContext = app.context
        self._widget: Widget | None = None

    def get_widget(self) -> Widget:
        """Return the page's root widget, built once and cached."""
        if self._widget is None:
            self._widget = self.build()
        return self._widget

    def build(self) -> Widget:
        """Build the widget tree (called once). Subclasses override this."""
        return Text(f"{self.title} (not implemented yet)")

    def on_show(self) -> None:
        """Called when the page becomes current (refresh dynamic data here)."""

    def on_notification(self, notification: Notification) -> None:
        """React to a backend notification while this page is current."""
