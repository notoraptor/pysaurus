"""Video card widget — one video: thumbnail, metadata and an actions menu.

Shows the thumbnail, metadata, a per-video actions menu (ContextButton) wired to
methods on the page, and a selection checkbox.
"""

from __future__ import annotations

import io

import videre
from PIL import Image
from videre.widgets.widget import Widget

from pysaurus.interface.videroid import theme
from pysaurus.video.video_pattern import VideoPattern

_THUMB_BOX = (180, 100)


def _thumb_frame(content: Widget) -> Widget:
    # Fixed-size centered frame (matches kyuti's QLabel.setFixedSize(180,100) +
    # AlignCenter): every card's thumbnail occupies the same box and the left
    # column aligns regardless of the video's aspect ratio. No border-radius
    # (videre gap G18).
    return videre.Container(
        content,
        width=_THUMB_BOX[0],
        height=_THUMB_BOX[1],
        horizontal_alignment=videre.Alignment.CENTER,
        vertical_alignment=videre.Alignment.CENTER,
        background_color="#e0e0e0",
        border=videre.Border.all(1, "#cccccc"),
    )


def _thumbnail(video: VideoPattern) -> Widget:
    data = video.thumbnail
    if not data:
        return _thumb_frame(
            videre.Text("(no thumbnail)", italic=True, color=videre.Colors.gray)
        )
    try:
        # Picture does not resize (videre gap G13): scale the JPEG via PIL first.
        image = Image.open(io.BytesIO(data))
        image.thumbnail(_THUMB_BOX)
        buffer = io.BytesIO()
        image.save(buffer, "PNG")
        picture = videre.Picture(buffer.getvalue())
    except Exception:
        picture = videre.Picture(data, alt="(thumbnail error)")
    return _thumb_frame(picture)


def _menu(video: VideoPattern, page) -> Widget:
    actions = [
        ("Toggle watched", lambda: page.video_toggle_watched(video)),
        ("Open", lambda: page.video_open(video)),
        ("Open folder", lambda: page.video_open_folder(video)),
        ("Copy title", lambda: page.video_copy(video, "title")),
        ("Copy file path", lambda: page.video_copy(video, "filename")),
        ("Copy video ID", lambda: page.video_copy(video, "video_id")),
        ("Rename...", lambda: page.video_rename(video)),
        ("Delete from database", lambda: page.video_delete_entry(video)),
        ("Move to Trash", lambda: page.video_trash(video)),
        ("Delete permanently", lambda: page.video_delete_file(video)),
    ]
    return videre.ContextButton("⚙", actions=actions, square=True)


def _attributes(
    video: VideoPattern, menu: Widget | None = None, checkbox: Widget | None = None
) -> Widget:
    # Bold + underlined, black (kyuti title_label: color #000000 with <b><u>).
    title = videre.Text(
        str(video.title),
        strong=True,
        underline=True,
        wrap=videre.TextWrap.WORD,
        weight=1,
    )
    leading = [w for w in (menu, checkbox) if w is not None]
    if leading:
        first = videre.Row(
            [*leading, title], space=5, vertical_alignment=videre.Alignment.CENTER
        )
    else:
        first = title
    rows: list[Widget] = [first]

    if video.meta_title:
        rows.append(videre.Text(str(video.file_title), italic=True, color="#666666"))
    # Filename in a colored box, two states (kyuti video_list_item.py:195-203).
    # Monospace is a videre gap (G17). Click-to-open / hover-underline deferred.
    watched = video.watched
    rows.append(
        videre.Container(
            videre.Text(
                str(video.filename),
                wrap=videre.TextWrap.CHAR,
                color="#a0a0a0" if watched else "#8c8cfa",
                italic=watched,
                strong=not watched,
            ),
            background_color="#f8f8f8" if watched else "#fafafa",
            border=None if watched else videre.Border.all(1, "#f0f0fa"),
            padding=videre.Padding.all(2),
        )
    )

    if video.readable:
        rows.append(
            videre.Text(
                f"{video.extension.upper()} {video.size} / {video.container_format} / "
                f"({video.video_codec}, {video.audio_codec}) / {video.byte_rate}/s",
                wrap=videre.TextWrap.WORD,
            )
        )
        rows.append(
            videre.Text(
                f"{video.length} | {video.width} x {video.height} @ "
                f"{round(video.frame_rate)} fps, {video.bit_depth} bits | "
                f"{video.sample_rate} Hz x {video.audio_bits or '?'} bits "
                f"({video.channels} channels), {video.audio_bit_rate_formatted}/s",
                wrap=videre.TextWrap.WORD,
            )
        )
        rows.append(
            videre.Text(
                f"Audio: {', '.join(video.audio_languages or ['(none)'])} | "
                f"Subtitles: {', '.join(video.subtitle_languages or ['(none)'])}"
            )
        )

    rows.append(
        videre.Text(
            f"{video.date} | (entry) {video.date_entry_modified} | "
            f"(opened) {video.date_entry_opened}",
            wrap=videre.TextWrap.WORD,
        )
    )

    status: list[Widget] = []
    if not video.found:
        status.append(videre.Text("NOT FOUND", color="#cc0000", strong=True))
    elif video.unreadable:
        status.append(videre.Text("Unreadable", color="#cc6600", strong=True))
    if video.watched:
        status.append(videre.Text("Watched", color="#008800"))
    if video.similarity_id is not None:
        status.append(videre.Text(f"Similarity: {video.similarity}", color="#0066cc"))
    if status:
        rows.append(
            videre.Row(status, space=10, vertical_alignment=videre.Alignment.CENTER)
        )

    if video.errors:
        rows.append(
            videre.Text(
                "Errors: " + "; ".join(video.errors),
                color="#cc0000",
                wrap=videre.TextWrap.WORD,
            )
        )

    if video.properties:
        rows.append(videre.Text("PROPERTIES", strong=True))
        for name, values in video.properties.items():
            rows.append(
                videre.Row(
                    [videre.Text(f"{name}:", strong=True, color="#666666")]
                    + [
                        # Value chip: #1976d2 underlined on #e3f2fd (kyuti:442-446).
                        # Click-to-filter deferred; wrapping (FlowLayout) is gap G16.
                        videre.Container(
                            videre.Text(str(value), color="#1976d2", underline=True),
                            background_color=theme.SELECTED_BG,
                            padding=videre.Padding.axis(vertical=1, horizontal=4),
                        )
                        for value in values
                    ],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                )
            )

    return videre.Column(rows, space=3, weight=1)


class VideoCard(videre.Container):
    __wprops__ = {}
    __slots__ = ()

    def __init__(
        self, video: VideoPattern, index: int = 0, page=None, selected: bool = False
    ):
        menu = _menu(video, page) if page is not None else None
        checkbox = (
            videre.Checkbox(
                checked=selected, data=video.video_id, on_change=page._on_card_check
            )
            if page is not None
            else None
        )
        # Per-state background + border, mirroring kyuti's VideoListItem styles
        # (no zebra striping — kyuti uses plain white for normal rows). Hover
        # states are deferred (need manual mouse_enter/exit tracking); border
        # radius is a videre gap (G18).
        if selected:
            bg, border = theme.SELECTED_BG, videre.Border.all(2, "#1976d2")
        elif not video.found:
            bg, border = "#fffde7", videre.Border.all(1, "#ffe082")
        else:
            bg, border = "#ffffff", videre.Border.all(1, "#dddddd")
        super().__init__(
            videre.Row(
                [_thumbnail(video), _attributes(video, menu, checkbox)], space=12
            ),
            padding=videre.Padding.all(8),
            background_color=bg,
            border=border,
        )
