"""Confirmation dialog with video thumbnail and file path."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from pysaurus.video.video_pattern import VideoPattern


class VideoConfirmDialog(QDialog):
    """Confirmation dialog showing video thumbnail and full file path."""

    def __init__(self, title: str, message: str, video: VideoPattern, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)

        # Top row: thumbnail + file path
        top = QHBoxLayout()

        # Thumbnail
        thumb_label = QLabel()
        thumb_label.setFixedSize(160, 90)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setStyleSheet(
            "background-color: #e0e0e0; border: 1px solid #ccc; border-radius: 2px;"
        )
        thumb_data = video.thumbnail
        if thumb_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(thumb_data):
                scaled = pixmap.scaled(
                    160,
                    90,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                thumb_label.setPixmap(scaled)
            else:
                thumb_label.setText("No preview")
        else:
            thumb_label.setText("No preview")
        top.addWidget(thumb_label)

        # File path in monospace
        path_label = QLabel(str(video.filename))
        path_label.setWordWrap(True)
        path_label.setFont(QFont("Consolas, Courier New, monospace", 9))
        path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        path_label.setStyleSheet(
            "padding: 4px;"
            "background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 3px;"
        )
        top.addWidget(path_label, 1)

        layout.addLayout(top)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("padding: 8px 0;")
        layout.addWidget(msg_label)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No
        )
        buttons.button(QDialogButtonBox.StandardButton.No).setDefault(True)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def confirm(title: str, message: str, video: VideoPattern, parent=None) -> bool:
        """Show the dialog and return True if user clicked Yes."""
        dialog = VideoConfirmDialog(title, message, video, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted
