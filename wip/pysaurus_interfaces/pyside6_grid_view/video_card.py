"""
Video card widget for displaying a video thumbnail and info.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
)

from pysaurus.video.video_pattern import VideoPattern


def _get_scaled_size(base_size: int, reference_font_size: int = 9) -> int:
    """
    Scale a size based on the application font size.

    Args:
        base_size: The base size designed for a 9pt font
        reference_font_size: The reference font size (default 9pt)

    Returns:
        Scaled size proportional to current app font
    """
    app = QApplication.instance()
    if app:
        current_font_size = app.font().pointSize()
        if current_font_size > 0:
            return int(base_size * current_font_size / reference_font_size)
    return base_size


class VideoCard(QFrame):
    """
    Card widget displaying a video thumbnail and basic info.

    Shows:
    - Thumbnail image
    - Title
    - Duration
    - Resolution
    - File size

    Emits signals on click and double-click.

    Uses light theme with sizes scaled to application font.
    """

    clicked = Signal(int, object)  # video_id, Qt.KeyboardModifiers
    double_clicked = Signal(int)  # video_id
    context_menu_requested = Signal(int, object)  # video_id, QPoint
    selection_changed = Signal(int, bool)  # video_id, selected

    # Base sizes (designed for 9pt font, will be scaled)
    BASE_THUMB_WIDTH = 200
    BASE_THUMB_HEIGHT = 112  # 16:9 ratio
    BASE_CARD_WIDTH = 220

    def __init__(self, video: VideoPattern, parent=None):
        super().__init__(parent)
        self.video = video
        self._selected = False

        # Calculate scaled sizes
        self._thumb_width = _get_scaled_size(self.BASE_THUMB_WIDTH)
        self._thumb_height = _get_scaled_size(self.BASE_THUMB_HEIGHT)
        self._card_width = _get_scaled_size(self.BASE_CARD_WIDTH)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        """Set up the UI components."""
        self.setFixedWidth(self._card_width)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(self._thumb_width, self._thumb_height)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet(
            "background-color: #e0e0e0; border: 1px solid #ccc; border-radius: 2px;"
        )
        self._load_thumbnail()
        layout.addWidget(self.thumb_label)

        # Duration badge
        self.duration_label = QLabel(str(self.video.length))
        self.duration_label.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0.75); color: white; "
            "padding: 2px 6px; border-radius: 2px;"
        )
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.duration_label)

        # Title row with checkbox (file_title in bold)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        self.checkbox = QCheckBox()
        self.checkbox.setToolTip(f"Select video {self.video.video_id}")
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        title_layout.addWidget(self.checkbox)

        file_title_str = str(self.video.file_title)
        self.title_label = QLabel(file_title_str)
        self.title_label.setToolTip(file_title_str)
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(_get_scaled_size(50))
        self.title_label.setStyleSheet(
            "color: #000000; font-weight: bold; text-decoration: underline;"
        )
        self.title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_label.mousePressEvent = self._on_title_clicked
        title_layout.addWidget(self.title_label, 1)

        layout.addLayout(title_layout)

        # Meta title in italic (if available)
        meta_title = self.video.meta_title
        if meta_title:
            meta_title_str = str(meta_title)
            self.meta_title_label = QLabel(meta_title_str)
            self.meta_title_label.setToolTip(meta_title_str)
            self.meta_title_label.setWordWrap(True)
            self.meta_title_label.setMaximumHeight(_get_scaled_size(40))
            self.meta_title_label.setStyleSheet("color: #666666; font-style: italic;")
            layout.addWidget(self.meta_title_label)

        # Info row: resolution and size
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)

        resolution = f"{self.video.width}x{self.video.height}"
        self.resolution_label = QLabel(resolution)
        self.resolution_label.setStyleSheet("color: #555555;")
        info_layout.addWidget(self.resolution_label)

        info_layout.addStretch()

        self.size_label = QLabel(str(self.video.size))
        self.size_label.setStyleSheet("color: #555555;")
        info_layout.addWidget(self.size_label)

        layout.addLayout(info_layout)

        # Status indicators
        status_parts = []
        if not self.video.found:
            status_parts.append('<span style="color: #cc0000;">Not found</span>')
        if not self.video.readable:
            status_parts.append('<span style="color: #cc6600;">Unreadable</span>')
        if self.video.watched:
            status_parts.append('<span style="color: #008800;">Watched</span>')

        if status_parts:
            status_label = QLabel(" | ".join(status_parts))
            status_label.setTextFormat(Qt.TextFormat.RichText)
            status_label.setStyleSheet("color: #666666;")
            layout.addWidget(status_label)

    def _load_thumbnail(self):
        """Load the thumbnail image."""
        thumb_data = self.video.thumbnail
        if thumb_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(thumb_data):
                scaled = pixmap.scaled(
                    self._thumb_width,
                    self._thumb_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.thumb_label.setPixmap(scaled)
                return

        # No thumbnail - show placeholder
        self.thumb_label.setText("No thumbnail")
        self.thumb_label.setStyleSheet(
            "background-color: #e0e0e0; color: #666666; border: 1px solid #ccc;"
        )

    def _apply_style(self):
        """Apply the card style (light theme)."""
        if self._selected:
            self.setStyleSheet("""
                VideoCard {
                    background-color: #e3f2fd;
                    border: 2px solid #1976d2;
                    border-radius: 6px;
                }
            """)
        elif not self.video.found:
            # Not found: light yellow background
            self.setStyleSheet("""
                VideoCard {
                    background-color: #fffde7;
                    border: 1px solid #ffe082;
                    border-radius: 6px;
                }
                VideoCard:hover {
                    border: 2px solid #ff9800;
                    background-color: #ffecb3;
                }
            """)
        else:
            self.setStyleSheet("""
                VideoCard {
                    background-color: #ffffff;
                    border: 1px solid #dddddd;
                    border-radius: 6px;
                }
                VideoCard:hover {
                    border: 2px solid #1976d2;
                    background-color: #e3f2fd;
                }
            """)

    @property
    def selected(self) -> bool:
        """Whether this card is selected."""
        return self._selected

    @selected.setter
    def selected(self, value: bool):
        """Set selection state."""
        if self._selected != value:
            self._selected = value
            # Update checkbox without triggering signal
            self.checkbox.blockSignals(True)
            self.checkbox.setChecked(value)
            self.checkbox.blockSignals(False)
            self._apply_style()

    def _on_checkbox_changed(self, state: int):
        """Handle checkbox state change."""
        checked = state == Qt.CheckState.Checked.value
        self._selected = checked
        self._apply_style()
        self.selection_changed.emit(self.video.video_id, checked)

    def _on_title_clicked(self, event):
        """Handle title label click - toggle checkbox."""
        self.checkbox.setChecked(not self.checkbox.isChecked())

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.video.video_id, event.modifiers())
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.video.video_id)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        """Handle context menu request."""
        self.context_menu_requested.emit(self.video.video_id, event.globalPos())
        super().contextMenuEvent(event)
