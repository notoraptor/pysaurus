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

    The only addition is a configurable callback for notifications,
    allowing AppContext to convert them to Qt signals.
    """

    __slots__ = ("_qt_notification_callback",)

    def __init__(self):
        super().__init__()
        self._qt_notification_callback = None

    def set_notification_callback(self, callback):
        """Configure the callback for notifications (used by AppContext)."""
        self._qt_notification_callback = callback

    def _notify(self, notification: Notification) -> None:
        """
        Implementation required by GuiAPI (abstract method).

        Routes notifications to the Qt callback if configured.
        """
        if self._qt_notification_callback:
            self._qt_notification_callback(notification)
