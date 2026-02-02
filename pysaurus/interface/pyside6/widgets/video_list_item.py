"""
Video list item widget for displaying a video with all its details.
"""

import re

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
    QWidget,
)

from pysaurus.interface.pyside6.widgets.flow_layout import FlowLayout

from pysaurus.video.video_pattern import VideoPattern

# Zero Width Space - allows line breaks without visible character
_ZWS = "\u200b"
# Pattern for characters after which we allow line breaks
_BREAK_PATTERN = re.compile(r"([\\/_\-.])")


def _add_break_opportunities(text: str) -> str:
    """Insert zero-width spaces after path separators and punctuation."""
    return _BREAK_PATTERN.sub(rf"\1{_ZWS}", text)


def _get_scaled_size(base_size: int, reference_font_size: int = 9) -> int:
    """Scale a size based on the application font size."""
    app = QApplication.instance()
    if app:
        current_font_size = app.font().pointSize()
        if current_font_size > 0:
            return int(base_size * current_font_size / reference_font_size)
    return base_size


class WrappingLabel(QLabel):
    """QLabel that correctly reports its height based on available width."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return super().heightForWidth(width)

    def sizeHint(self):
        hint = super().sizeHint()
        if hint.width() > 400:
            hint.setWidth(400)
            hint.setHeight(self.heightForWidth(400))
        return hint


class VideoListItem(QFrame):
    """
    List item widget displaying a video with thumbnail and all details.

    Layout:
    [Thumbnail] | Title
                | Filename
                | EXT | size / container (video_codec, audio_codec) | Bit rate: X/s
                | duration | WxH @ fps, bits | sample_rate Hz (channels), audio Kb/s
                | date | (entry) date_entry_modified | (opened) date_entry_opened
                | Audio: langs | Subtitles: langs
                | Similarity ID: X

    Uses light theme with sizes scaled to application font.
    """

    clicked = Signal(int, object)  # video_id, modifiers
    double_clicked = Signal(int)  # video_id
    context_menu_requested = Signal(int, object)  # video_id, QPoint
    selection_changed = Signal(int, bool)  # video_id, selected
    property_value_clicked = Signal(str, object)  # prop_name, value

    # Base sizes (designed for 9pt font, will be scaled)
    BASE_THUMB_WIDTH = 180
    BASE_THUMB_HEIGHT = 100

    # Highlight color for differing fields (works on white and yellow backgrounds)
    DIFF_HIGHLIGHT = "#ffcccc"  # Light pink/salmon
    CHAR_DIFF_HIGHLIGHT = "#ff9999"  # Slightly darker pink for character-level diffs

    def __init__(
        self,
        video: VideoPattern,
        diff_fields: set[str] | None = None,
        file_title_diffs: list[tuple[int, int]] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.video = video
        self._selected = False
        self._diff_fields = diff_fields or set()
        self._file_title_diffs = file_title_diffs  # Character ranges that differ

        # Calculate scaled sizes
        self._thumb_width = _get_scaled_size(self.BASE_THUMB_WIDTH)
        self._thumb_height = _get_scaled_size(self.BASE_THUMB_HEIGHT)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        """Set up the UI components."""
        # Preferred height policy - allows WrappingLabels to adjust height correctly
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)

        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(self._thumb_width, self._thumb_height)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet(
            "background-color: #e0e0e0; border: 1px solid #ccc; border-radius: 2px;"
        )
        self._load_thumbnail()
        main_layout.addWidget(self.thumb_label)

        # Details on the right
        details_layout = QVBoxLayout()
        details_layout.setSpacing(3)
        details_layout.setContentsMargins(0, 0, 0, 0)

        # Row 1: Checkbox + Title
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(4)

        self.checkbox = QCheckBox()
        self.checkbox.setToolTip(f"Select video {self.video.video_id}")
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        title_row.addWidget(self.checkbox)

        # Note: title = meta_title or file_title, so when meta_title is empty,
        # title == file_title. In that case, apply character-level diffs to title.
        title_str = str(self.video.title)
        file_title = str(self.video.file_title)
        title_is_file_title = title_str == file_title

        # Apply character-level diff highlights if title is actually file_title
        if title_is_file_title and self._file_title_diffs:
            # _apply_char_diff_highlights now handles break opportunities internally
            title_display = self._apply_char_diff_highlights(title_str)
            title_html = f'<b><u>{title_display}</u></b>'
        else:
            title_display = _add_break_opportunities(self._escape_html(title_str))
            title_html = self._highlight_if_diff("title", f'<b><u>{title_display}</u></b>')

        self.title_label = WrappingLabel(title_html)
        self.title_label.setToolTip(title_str)
        self.title_label.setTextFormat(Qt.TextFormat.RichText)
        self.title_label.setStyleSheet("color: #000000;")
        self.title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_label.mousePressEvent = self._on_title_clicked
        title_row.addWidget(self.title_label, 1)

        details_layout.addLayout(title_row)

        # Row 2: Filename (if different from title)
        if file_title and not title_is_file_title:
            # Apply character-level diff highlights (handles escaping + break opportunities)
            if self._file_title_diffs:
                # _apply_char_diff_highlights now handles break opportunities internally
                file_title_display = self._apply_char_diff_highlights(file_title)
            else:
                file_title_display = _add_break_opportunities(
                    self._escape_html(file_title)
                )
            file_title_label = WrappingLabel(f"<i>{file_title_display}</i>")
            file_title_label.setStyleSheet("color: #666666;")
            file_title_label.setTextFormat(Qt.TextFormat.RichText)
            details_layout.addWidget(file_title_label)

        # Row 3: Filename path (blue-violet like web interface, gray if watched)
        filename = str(self.video.filename) if self.video.filename else ""
        filename_display = _add_break_opportunities(self._escape_html(filename))
        if self.video.watched:
            # Already watched: gray italic
            filename_label = WrappingLabel(f"<code><i>{filename_display}</i></code>")
            filename_label.setStyleSheet(
                "color: #a0a0a0; background-color: #f8f8f8; padding: 2px;"
            )
        else:
            # Not watched: blue-violet bold
            filename_label = WrappingLabel(f"<code>{filename_display}</code>")
            filename_label.setStyleSheet(
                "color: #8c8cfa; font-weight: bold; background-color: #fafafa; "
                "border: 1px solid #f0f0fa; padding: 2px;"
            )
        filename_label.setTextFormat(Qt.TextFormat.RichText)
        details_layout.addWidget(filename_label)

        # Row 4: Format line with badges
        ext = str(self.video.extension).upper() if self.video.extension else ""
        size = str(self.video.size) if hasattr(self.video, "size") else ""
        container = self.video.container_format or ""
        video_codec = self.video.video_codec or ""
        audio_codec = self.video.audio_codec or ""
        bit_rate = str(self.video.bit_rate) if hasattr(self.video, "bit_rate") else ""

        # Badge style: white text on dark background (using &nbsp; for padding since Qt ignores CSS padding)
        badge = "background-color: #333; color: white; font-weight: bold;"
        ext_html = self._highlight_if_diff(
            "extension", f'<span style="{badge}">&nbsp;&nbsp;{ext}&nbsp;&nbsp;</span>'
        )
        size_html = self._highlight_if_diff("size", f"<b>{size}</b>")
        container_html = self._highlight_if_diff("container_format", container)
        video_codec_html = self._highlight_if_diff(
            "video_codec", f'<span style="color: #666;">{video_codec}</span>'
        )
        audio_codec_html = self._highlight_if_diff(
            "audio_codec", f'<span style="color: #666;">{audio_codec}</span>'
        )
        bit_rate_html = self._highlight_if_diff(
            "bit_rate", f"<b><i>{bit_rate}/s</i></b>"
        )
        format_line = (
            f"{ext_html} "
            f"{size_html} / {container_html} "
            f"({video_codec_html}, {audio_codec_html}) "
            f'<span style="{badge}">&nbsp;Bit rate&nbsp;</span> '
            f"{bit_rate_html}"
        )
        format_label = WrappingLabel(format_line)
        format_label.setTextFormat(Qt.TextFormat.RichText)
        format_label.setStyleSheet("color: #333333;")
        details_layout.addWidget(format_label)

        # Row 5: Duration | Resolution @ fps, bits | Audio specs
        duration = str(self.video.length) if hasattr(self.video, "length") else ""
        width = self.video.width or 0
        height = self.video.height or 0
        frame_rate = round(self.video.frame_rate) if self.video.frame_rate else 0
        bit_depth = self.video.bit_depth or 8
        sample_rate = self.video.sample_rate or 0
        audio_bits = getattr(self.video, "audio_bits", None) or 32
        channels = self.video.channels or 0
        audio_bit_rate_kbps = (
            round(self.video.audio_bit_rate / 1000) if self.video.audio_bit_rate else 0
        )

        duration_html = self._highlight_if_diff(
            "length", f'<b style="color: #0066cc;">{duration}</b>'
        )
        width_html = self._highlight_if_diff(
            "width", f'<b style="color: #006600;">{width}</b>'
        )
        height_html = self._highlight_if_diff(
            "height", f'<b style="color: #006600;">{height}</b>'
        )
        frame_rate_html = self._highlight_if_diff("frame_rate", f"{frame_rate} fps")
        bit_depth_html = self._highlight_if_diff("bit_depth", f"{bit_depth} bits")
        sample_rate_html = self._highlight_if_diff("sample_rate", f"{sample_rate} Hz")
        audio_bits_html = self._highlight_if_diff("audio_bits", f"{audio_bits} bits")
        channels_html = self._highlight_if_diff("channels", f"{channels} ch")
        audio_bit_rate_html = self._highlight_if_diff(
            "audio_bit_rate", f"{audio_bit_rate_kbps} Kb/s"
        )

        video_line = (
            f"{duration_html} | "
            f"{width_html} x {height_html} "
            f'@ <span style="color: #666;">{frame_rate_html}, {bit_depth_html}</span> | '
            f'<span style="color: #666;">{sample_rate_html} x {audio_bits_html} '
            f"({channels_html}), {audio_bit_rate_html}</span>"
        )
        video_label = WrappingLabel(video_line)
        video_label.setTextFormat(Qt.TextFormat.RichText)
        video_label.setStyleSheet("color: #333333;")
        details_layout.addWidget(video_label)

        # Row 6: Dates
        date = str(self.video.date) if hasattr(self.video, "date") else ""
        date_entry_modified = (
            str(self.video.date_entry_modified)
            if self.video.date_entry_modified
            else ""
        )
        date_entry_opened = (
            str(self.video.date_entry_opened)
            if hasattr(self.video, "date_entry_opened") and self.video.date_entry_opened
            else ""
        )

        date_html = self._highlight_if_diff(
            "date", f'<code style="color: #996600;">{date}</code>'
        )
        date_line = date_html
        if date_entry_modified:
            date_mod_html = self._highlight_if_diff(
                "date_entry_modified",
                f'<code style="color: #996600;">{date_entry_modified}</code>',
            )
            date_line += f' | <i style="color: #888;">(entry)</i> {date_mod_html}'
        if date_entry_opened:
            date_opened_html = self._highlight_if_diff(
                "date_entry_opened",
                f'<code style="color: #996600;">{date_entry_opened}</code>',
            )
            date_line += f' | <i style="color: #888;">(opened)</i> {date_opened_html}'

        date_label = WrappingLabel(date_line)
        date_label.setTextFormat(Qt.TextFormat.RichText)
        details_layout.addWidget(date_label)

        # Row 7: Audio/Subtitle languages
        audio_langs = getattr(self.video, "audio_languages", None) or []
        subtitle_langs = getattr(self.video, "subtitle_languages", None) or []
        audio_str = (
            ", ".join(audio_langs)
            if audio_langs
            else '<span style="color: #aaa;">(none)</span>'
        )
        subtitle_str = (
            ", ".join(subtitle_langs)
            if subtitle_langs
            else '<span style="color: #aaa;">(none)</span>'
        )

        audio_langs_html = self._highlight_if_diff("audio_languages", audio_str)
        subtitle_langs_html = self._highlight_if_diff(
            "subtitle_languages", subtitle_str
        )
        lang_line = (
            f'<b style="color: #333;">Audio:</b> {audio_langs_html} | '
            f'<b style="color: #333;">Subtitles:</b> {subtitle_langs_html}'
        )
        lang_label = WrappingLabel(lang_line)
        lang_label.setTextFormat(Qt.TextFormat.RichText)
        lang_label.setStyleSheet("color: #555555;")
        details_layout.addWidget(lang_label)

        # Row 8: Status indicators (with colors for light theme)
        status_parts = []
        if not self.video.found:
            status_parts.append(
                '<span style="color: #cc0000; font-weight: bold;">NOT FOUND</span>'
            )
        if not self.video.readable:
            status_parts.append(
                '<span style="color: #cc6600; font-weight: bold;">Unreadable</span>'
            )
        if self.video.watched:
            status_parts.append('<span style="color: #008800;">Watched</span>')
        if self.video.similarity_id is not None:
            if self.video.similarity_id == -1:
                status_parts.append(
                    '<span style="color: #666666;">Similarity: (no match)</span>'
                )
            else:
                status_parts.append(
                    f'<span style="color: #0066cc;">Similarity ID: {self.video.similarity_id}</span>'
                )

        if status_parts:
            status_label = WrappingLabel(" | ".join(status_parts))
            status_label.setTextFormat(Qt.TextFormat.RichText)
            details_layout.addWidget(status_label)

        # Row 9: Errors (if any)
        errors = getattr(self.video, "errors", None) or []
        if errors:
            errors_label = WrappingLabel(
                f'<span style="color: #cc0000;"><b>Errors:</b> {", ".join(str(e) for e in errors)}</span>'
            )
            errors_label.setTextFormat(Qt.TextFormat.RichText)
            details_layout.addWidget(errors_label)

        # Row 10: Custom properties (compact, only non-empty) - clickable values
        properties = getattr(self.video, "properties", None) or {}
        has_properties = False
        for prop_name, prop_values in properties.items():
            # Filter out None and empty values
            values = [v for v in prop_values if v is not None]
            if values:
                has_properties = True
                break

        if has_properties:
            # Use FlowLayout for wrapping
            props_widget = QWidget()
            props_layout = FlowLayout(props_widget, margin=4, h_spacing=4, v_spacing=2)

            for prop_name, prop_values in properties.items():
                values = [v for v in prop_values if v is not None]
                if not values:
                    continue

                # Property name label
                name_label = QLabel(f"<b>{self._escape_html(prop_name)}:</b>")
                name_label.setTextFormat(Qt.TextFormat.RichText)
                name_label.setStyleSheet("color: #666;")
                props_layout.addWidget(name_label)

                # Clickable value labels
                for value in values:
                    value_label = QLabel(str(value))
                    value_label.setStyleSheet(
                        "color: #1976d2; text-decoration: underline; "
                        "background-color: #e3f2fd; padding: 1px 4px; "
                        "border-radius: 3px;"
                    )
                    value_label.setCursor(Qt.CursorShape.PointingHandCursor)
                    value_label.setToolTip(f"Filter by {prop_name} = {value}")
                    # Capture prop_name and value for the lambda
                    value_label.mousePressEvent = (
                        lambda e, pn=prop_name, v=value: self._on_property_value_clicked(pn, v)
                    )
                    props_layout.addWidget(value_label)

            # Style the container
            props_widget.setStyleSheet(
                "background-color: #f5f5f5; border-radius: 2px;"
            )
            details_layout.addWidget(props_widget)

        main_layout.addLayout(details_layout, 1)

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

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def _highlight_if_diff(self, field: str, html: str) -> str:
        """Wrap HTML with highlight style if field differs from other videos in group."""
        if field in self._diff_fields:
            return f'<span style="background-color: {self.DIFF_HIGHLIGHT}; padding: 1px 3px;">{html}</span>'
        return html

    def _apply_char_diff_highlights(self, text: str) -> str:
        """Apply character-level diff highlights to text.

        Takes diff ranges (start, end) and wraps those character ranges in
        highlight spans. The text should be the ORIGINAL (non-escaped) text,
        as the diff ranges are computed on the original string.

        Each segment is escaped and has break opportunities added individually,
        BEFORE wrapping in HTML spans (to avoid breaking CSS properties).
        """
        if not self._file_title_diffs:
            return _add_break_opportunities(self._escape_html(text))

        # Sort ranges by start position (in case they're not sorted)
        ranges = sorted(self._file_title_diffs)

        # Build result by interleaving normal and highlighted text
        result = []
        pos = 0

        for start, end in ranges:
            # Add normal text before this diff range (escaped + break opportunities)
            if start > pos:
                segment = _add_break_opportunities(self._escape_html(text[pos:start]))
                result.append(segment)
            # Add highlighted diff range (escaped + break opportunities, then wrapped)
            diff_text = _add_break_opportunities(self._escape_html(text[start:end]))
            result.append(
                f'<span style="background-color: {self.CHAR_DIFF_HIGHLIGHT}; '
                f'font-weight: bold;">{diff_text}</span>'
            )
            pos = end

        # Add remaining text after last diff range (escaped + break opportunities)
        if pos < len(text):
            result.append(_add_break_opportunities(self._escape_html(text[pos:])))

        return "".join(result)

    def _apply_style(self):
        """Apply the item style (light theme)."""
        if self._selected:
            self.setStyleSheet("""
                VideoListItem {
                    background-color: #e3f2fd;
                    border: 2px solid #1976d2;
                    border-radius: 6px;
                }
            """)
        elif not self.video.found:
            # Not found: light yellow background
            # previous:
            # border-color: #ffb300;
            # background-color: #fff8e1;
            self.setStyleSheet("""
                VideoListItem {
                    background-color: #fffde7;
                    border: 1px solid #ffe082;
                    border-radius: 6px;
                }
                VideoListItem:hover {
                    border: 2px solid #ff9800;
                    background-color: #ffecb3;
                }
            """)
        else:
            # previous:
            # border-color: #999999;
            # background-color: #fafafa;
            self.setStyleSheet("""
                VideoListItem {
                    background-color: #ffffff;
                    border: 1px solid #dddddd;
                    border-radius: 6px;
                }
                VideoListItem:hover {
                    border: 2px solid #1976d2;
                    background-color: #e3f2fd;
                }
            """)

    @property
    def selected(self) -> bool:
        """Whether this item is selected."""
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

    def _on_property_value_clicked(self, prop_name: str, value):
        """Handle property value click - emit signal to filter by this value."""
        self.property_value_clicked.emit(prop_name, value)

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
