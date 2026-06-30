"""QMenu subclass that only triggers actions on left-click."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu


class LeftClickMenu(QMenu):
    """A QMenu that ignores right-click releases.

    By default, QMenu triggers the hovered action on any mouse button release,
    including right-click. This subclass ensures only left-click triggers actions.
    """

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)
