"""
PySide6 implementation of GuiAPI.

Extends GuiAPI to provide Qt-compatible notification handling.
"""

from pysaurus.core.notifications import Notification
from pysaurus.interface.api.gui_api import GuiAPI


class PySide6API(GuiAPI):
    """
    PySide6 implementation of GuiAPI.

    Inherits all functionality from GuiAPI:
    - Threading via @process decorator (create_database, open_database, etc.)
    - Notification system
    - All methods from FeatureAPI and GuiAPI

    Additions:
    - Configurable callback for notifications (AppContext -> Qt signals)
    - Configurable callback for exceptions from background threads
    - Overridden _run_thread() to catch and transfer exceptions to main thread
    """

    __slots__ = ("_qt_notification_callback", "_exception_callback")

    def __init__(self):
        super().__init__()
        self._qt_notification_callback = None
        self._exception_callback = None

    def set_notification_callback(self, callback):
        """Configure the callback for notifications (used by AppContext)."""
        self._qt_notification_callback = callback

    def set_exception_callback(self, callback):
        """Configure the callback for exceptions from background threads."""
        self._exception_callback = callback

    def _notify(self, notification: Notification) -> None:
        """
        Implementation required by GuiAPI (abstract method).

        Routes notifications to the Qt callback if configured.
        """
        if self._qt_notification_callback:
            self._qt_notification_callback(notification)

    def _run_thread(self, function, *args, **kwargs):
        """Override to transfer exceptions from background threads to main thread."""

        def wrapper():
            try:
                function(*args, **kwargs)
            except Exception as exc:
                if self._exception_callback:
                    self._exception_callback(exc)

        return super()._run_thread(wrapper)
