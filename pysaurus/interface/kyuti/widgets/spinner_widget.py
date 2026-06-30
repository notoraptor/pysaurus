"""Animated spinner (progress ring) widget."""

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class SpinnerWidget(QWidget):
    """Circular indeterminate progress indicator (spinning ring)."""

    def __init__(self, size: int = 48, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._complete = False
        self._color = QColor("#0078d4")
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(30)

    def _rotate(self):
        self._angle = (self._angle - 6) % 360
        self.update()

    def stop(self):
        """Stop the spinner and show a full ring (complete)."""
        self._timer.stop()
        self._complete = True
        self.update()

    def paintEvent(self, event):
        size = min(self.width(), self.height())
        margin = 4
        rect = QRect(margin, margin, size - 2 * margin, size - 2 * margin)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background track
        track_pen = QPen(QColor("#e0e0e0"), 4)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, 0, 360 * 16)

        # Foreground: full ring + checkmark when complete, spinning arc otherwise
        arc_pen = QPen(self._color, 4)
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)
        if self._complete:
            painter.drawArc(rect, 0, 360 * 16)
            # Checkmark in the center
            cx = size / 2
            cy = size / 2
            s = size * 0.18  # scale factor for checkmark
            check_pen = QPen(QColor("#4CAF50"), 3)
            check_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            check_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(check_pen)
            painter.drawLine(int(cx - s * 1.1), int(cy), int(cx - s * 0.1), int(cy + s))
            painter.drawLine(
                int(cx - s * 0.1), int(cy + s), int(cx + s * 1.3), int(cy - s * 0.8)
            )
        else:
            painter.drawArc(rect, self._angle * 16, 90 * 16)

        painter.end()
