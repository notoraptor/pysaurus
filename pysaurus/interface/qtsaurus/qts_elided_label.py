from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QLabel


class QtsElidedLabel(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.original_text = text
        self._update_text()

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self._update_text()

    def minimumSizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(0, super().minimumSizeHint().height())

    def _update_text(self):
        metrics = QtGui.QFontMetrics(self.font())
        elided_text = metrics.elidedText(
            self.original_text, QtCore.Qt.TextElideMode.ElideRight, self.width()
        )
        self.setText(elided_text)
