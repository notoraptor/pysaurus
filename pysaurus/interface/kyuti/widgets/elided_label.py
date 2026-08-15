"""Label that shortens its text with an ellipsis instead of overflowing."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFontMetrics, QResizeEvent
from PySide6.QtWidgets import QLabel


class ElidedLabel(QLabel):
    """QLabel whose text is elided to the right when too narrow.

    ``minimumSizeHint`` drops the width requirement, so a layout may squeeze
    this label down to nothing instead of pushing its siblings out of view.
    """

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.original_text = text
        self._update_text()

    def setText(self, text: str) -> None:
        self.original_text = text
        self._update_text()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._update_text()

    def minimumSizeHint(self) -> QSize:
        return QSize(0, super().minimumSizeHint().height())

    def _update_text(self):
        metrics = QFontMetrics(self.font())
        super().setText(
            metrics.elidedText(
                self.original_text, Qt.TextElideMode.ElideRight, self.width()
            )
        )
