"""Video card widget — one video: thumbnail, metadata and an actions menu.

Shows the thumbnail, metadata, a per-video actions menu (ContextButton) wired to
methods on the page, and a selection checkbox.
"""

from __future__ import annotations

import io

import videre
from PIL import Image
from videre.widgets.widget import Widget

from pysaurus.video.video_pattern import VideoPattern

_EVEN_BG = videre.parse_color((245, 245, 245))
_SELECTED_BG = videre.parse_color((227, 242, 253))
_BADGE_BG = videre.parse_color((240, 240, 240))
_THUMB_BOX = (180, 100)


def _thumbnail(video: VideoPattern) -> Widget:
    data = video.thumbnail
    if not data:
        return videre.Container(
            videre.Text("(no thumbnail)", italic=True),
            width=_THUMB_BOX[0],
            height=_THUMB_BOX[1],
            horizontal_alignment=videre.Alignment.CENTER,
            vertical_alignment=videre.Alignment.CENTER,
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
    return videre.Container(picture, horizontal_alignment=videre.Alignment.CENTER)


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
    title = videre.Text(
        str(video.title), strong=True, wrap=videre.TextWrap.WORD, weight=1
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
        rows.append(
            videre.Text(str(video.file_title), italic=True, color=videre.Colors.gray)
        )
    rows.append(
        videre.Text(
            str(video.filename),
            wrap=videre.TextWrap.CHAR,
            color=videre.Colors.gray if video.watched else videre.Colors.blueviolet,
            italic=video.watched,
            strong=not video.watched,
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
        status.append(videre.Text("NOT FOUND", color=videre.Colors.red, strong=True))
    elif video.unreadable:
        status.append(
            videre.Text("Unreadable", color=videre.Colors.darkorange, strong=True)
        )
    if video.watched:
        status.append(videre.Text("Watched", color=videre.Colors.green))
    if video.similarity_id is not None:
        status.append(videre.Text(f"Similarity: {video.similarity}"))
    if status:
        rows.append(
            videre.Row(status, space=10, vertical_alignment=videre.Alignment.CENTER)
        )

    if video.errors:
        rows.append(
            videre.Text(
                "Errors: " + "; ".join(video.errors),
                color=videre.Colors.red,
                wrap=videre.TextWrap.WORD,
            )
        )

    if video.properties:
        rows.append(videre.Text("PROPERTIES", strong=True))
        for name, values in video.properties.items():
            rows.append(
                videre.Row(
                    [videre.Text(f"{name}:", strong=True)]
                    + [
                        videre.Container(
                            videre.Text(str(value), italic=True),
                            background_color=_BADGE_BG,
                            padding=videre.Padding.axis(vertical=2, horizontal=10),
                        )
                        for value in values
                    ],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                )
            )

    return videre.Column(rows, space=2, weight=1)


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
        super().__init__(
            videre.Row(
                [_thumbnail(video), _attributes(video, menu, checkbox)], space=6
            ),
            padding=videre.Padding.axis(vertical=8, horizontal=4),
            background_color=(
                _SELECTED_BG if selected else (_EVEN_BG if index % 2 == 1 else None)
            ),
        )
