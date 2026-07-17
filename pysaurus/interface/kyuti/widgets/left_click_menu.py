"""QMenu subclass that only triggers actions on left-click."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QMenu, QProxyStyle, QStyle, QStyleOptionMenuItem

# Text color used for "danger" (destructive) menu entries.
_DANGER_COLOR = QColor("#c0392b")
# Brighter variant kept readable over the selection highlight background.
_DANGER_COLOR_SELECTED = QColor("#ff6b6b")


class _DangerMenuStyle(QProxyStyle):
    """Proxy style that repaints menu items flagged as "danger" in red.

    The flag is carried by the ``QAction`` via ``action.setProperty("danger",
    True)``. ``QStyleOptionMenuItem`` does not expose the originating action, so
    we match it back through the drawn menu's own actions by text.
    """

    def drawControl(self, element, option, painter, widget=None):
        if element == QStyle.ControlElement.CE_MenuItem and self._is_danger(
            widget, option
        ):
            # Copy so we never mutate the option Qt still owns.
            option = QStyleOptionMenuItem(option)
            palette = option.palette
            # Set every role a style might use for the label, in every state:
            # Fusion uses HighlightedText when the item is hovered, while the
            # Windows styles keep a light background and draw the text with the
            # plain Text/ButtonText roles even when hovered.
            palette.setColor(QPalette.ColorRole.Text, _DANGER_COLOR)
            palette.setColor(QPalette.ColorRole.ButtonText, _DANGER_COLOR)
            palette.setColor(QPalette.ColorRole.HighlightedText, _DANGER_COLOR_SELECTED)
            option.palette = palette
        super().drawControl(element, option, painter, widget)

    @staticmethod
    def _is_danger(widget, option) -> bool:
        if not isinstance(widget, QMenu):
            return False
        for action in widget.actions():
            if action.text() == option.text and action.property("danger"):
                return True
        return False


class LeftClickMenu(QMenu):
    """A QMenu that ignores right-click releases.

    By default, QMenu triggers the hovered action on any mouse button release,
    including right-click. This subclass ensures only left-click triggers actions.

    It also understands two extra keyword arguments on :meth:`addAction`:
    ``danger`` (red text, for destructive actions) and ``bold``.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Kept as an attribute so it is not garbage-collected while in use.
        self._danger_style = _DangerMenuStyle()
        self.setStyle(self._danger_style)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)

    def addAction(self, *args, danger: bool = False, bold: bool = False):
        action = super().addAction(*args)
        if action is None:
            return action
        if danger:
            action.setProperty("danger", True)
        if bold:
            font = action.font()
            font.setBold(True)
            action.setFont(font)
        return action
