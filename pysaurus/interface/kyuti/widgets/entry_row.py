"""Building block for list rows carrying their own action buttons."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

ROW_BUTTON_STYLE = (
    "QPushButton { padding: 1px 5px; min-width: 20px; }"
    "QPushButton:hover { background-color: #0078d4; color: white; }"
)


def make_row_button(text: str, tooltip: str, value, slot: Callable) -> QPushButton:
    """Build the action button of a row, placed before the value it acts on.

    ``slot`` must be a bound method (not a lambda) to avoid PySide6 GC; it reads
    the row value back with ``self.sender().property("value")``.
    """
    button = QPushButton(text)
    # Never take focus: destroying a focused row hands focus to the next one,
    # scrolling the view away from where the user just clicked.
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.setToolTip(tooltip)
    button.setStyleSheet(ROW_BUTTON_STYLE)
    button.setFixedWidth(24)
    button.setProperty("value", value)
    button.clicked.connect(slot)
    return button
