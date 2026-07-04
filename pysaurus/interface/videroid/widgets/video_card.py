"""Video card widget — one video: thumbnail, metadata and an actions menu.

Shows the thumbnail, metadata, a per-video actions menu (ContextButton) wired to
methods on the page, and a selection checkbox. The card is interactive (mirrors
kyuti's VideoListItem): it tracks hover to switch among the 6 visual states, and
its title / filename / property chips are clickable (toggle selection / open /
filter by value).
"""

from __future__ import annotations

import videre
from videre.core.events import MouseButton, MouseEvent
from videre.layouts.control_layout import ControlLayout
from videre.widgets.widget import Widget

from pysaurus.interface.videroid import theme
from pysaurus.video.video_pattern import VideoPattern

_THUMB_BOX = (180, 100)


class _Clickable(ControlLayout):
    """Transparent single-child wrapper that makes its child left-clickable and,
    optionally, hover-aware.

    videre's ``Div`` is the usual clickable, but it carries its own 3-state
    style + padding + inner Container we don't want inside a card. ``_Clickable``
    just captures the mouse and forwards left-click and hover to plain
    callbacks, so the card can wire the title (toggle), the filename (open +
    hover-underline) and each property chip (filter) without a styled ``Div``.

    It deliberately does NOT capture ``mouse_enter``/``mouse_exit`` (the handlers
    return ``None``), so the enclosing ``VideoCard`` still receives them and
    keeps its own hover state while the cursor is over a clickable child (videre
    emits enter/exit along the whole owner lineage, not just the owner).
    """

    __wprops__ = {}
    __slots__ = ("_on_click", "_on_hover")
    __capture_mouse__ = True

    def __init__(self, control: Widget, on_click, on_hover=None, **kwargs):
        super().__init__(control, **kwargs)
        self._on_click = on_click
        self._on_hover = on_hover

    def handle_click(self, button: MouseButton):
        if button == MouseButton.BUTTON_LEFT:
            # call_now defers the mutation out of the event dispatch, exactly
            # like Div.click (a filter click rebuilds the whole page).
            self.get_window().call_now(self._on_click)
        return self

    def handle_mouse_enter(self, event: MouseEvent):
        if self._on_hover is not None:
            self._on_hover(True)

    def handle_mouse_exit(self):
        if self._on_hover is not None:
            self._on_hover(False)


def _card_style(selected: bool, hovered: bool, found: bool) -> tuple[str, int, str]:
    """The 6 kyuti VideoListItem states (video_list_item.py:543-554) as
    ``(background, border_width, border_color)``. kyuti's ``border-radius: 6`` is
    dropped (videre gap G18); ``selected`` bg ``#e3f2fd`` == ``theme.SELECTED_BG``.
    """
    if selected and hovered:
        return "#d0e8fc", 2, "#1565c0"
    if selected:
        return "#e3f2fd", 2, "#1976d2"
    if hovered and not found:
        return "#ffecb3", 2, "#ff9800"
    if not found:
        return "#fffde7", 1, "#ffe082"
    if hovered:
        return "#f5f9ff", 1, "#90caf9"
    return "#ffffff", 1, "#dddddd"


def _thumb_frame(content: Widget, box: tuple[int, int] = _THUMB_BOX) -> Widget:
    # Fixed-size centered frame (matches kyuti's QLabel.setFixedSize(180,100) +
    # AlignCenter): every card's thumbnail occupies the same box and the left
    # column aligns regardless of the video's aspect ratio. No border-radius
    # (videre gap G18). `box` is parameterized so the delete-confirm can reuse
    # this at 160x90 (kyuti's video_confirm thumbnail).
    return videre.Container(
        content,
        width=box[0],
        height=box[1],
        horizontal_alignment=videre.Alignment.CENTER,
        vertical_alignment=videre.Alignment.CENTER,
        background_color="#e0e0e0",
        border=videre.Border.all(1, "#cccccc"),
    )


def _thumbnail(video: VideoPattern, box: tuple[int, int] = _THUMB_BOX) -> Widget:
    data = video.thumbnail
    if not data:
        return _thumb_frame(
            videre.Text("(no thumbnail)", italic=True, color=videre.Colors.gray), box
        )
    # The raw JPEG goes straight to videre with its logical display box
    # (kyuti: QPixmap.scaled KeepAspectRatio): the renderer resamples the
    # native bitmap once, directly to device pixels, so the thumbnail is as
    # sharp as the source allows on any display scale. Undecodable bytes fall
    # back to the alt text (Picture handles it).
    picture = videre.Picture(
        data, alt="(thumbnail error)", width=box[0], height=box[1], keep_ratio=True
    )
    return _thumb_frame(picture, box)


def _menu(video: VideoPattern, page) -> Widget:
    actions = [
        ("Toggle watched", lambda: page.video_toggle_watched(video)),
        ("Open", lambda: page.video_open(video)),
        ("Open in VLC", lambda: page.video_open_vlc(video)),
        ("Open folder", lambda: page.video_open_folder(video)),
        ("Copy title", lambda: page.video_copy(video, "title")),
        ("Copy file title", lambda: page.video_copy(video, "file_title")),
        ("Copy file path", lambda: page.video_copy(video, "filename")),
        ("Copy video ID", lambda: page.video_copy(video, "video_id")),
        ("Rename...", lambda: page.video_rename(video)),
        ("Move to...", lambda: page.video_move(video)),
    ]
    # Similarity actions, only when the video carries a (re-encoded) similarity
    # id (kyuti: Dismiss only for a real match >= 0, Reset always).
    for field, label in (
        ("similarity_id", "similarity"),
        ("similarity_id_reencoded", "re-encoded similarity"),
    ):
        value = getattr(video, field, None)
        if value is None:
            continue
        if value >= 0:
            actions.append(
                (
                    f"Dismiss {label}",
                    lambda f=field: page.video_dismiss_similarity(video, f),
                )
            )
        actions.append(
            (f"Reset {label}", lambda f=field: page.video_reset_similarity(video, f))
        )
    # Generalize-title items, only while the page is grouped by a similarity
    # field with several videos shown (kyuti videos_page.py:1427): copy this
    # video's title into a property for the other videos of the group.
    if page.grouped_by_similarity():
        if video.meta_title:
            actions.append(
                (
                    "Generalize meta title into property...",
                    lambda: page.video_generalize_title(video, "meta_title"),
                )
            )
        actions.append(
            (
                "Generalize file title into property...",
                lambda: page.video_generalize_title(video, "file_title"),
            )
        )
    # Move confirmations: one flat item per candidate destination (kyuti has a
    # "Confirm move to" submenu; videre menus are flat, G10). `moves` is set on
    # missing videos that have potential found destinations.
    for move in video.moves or []:
        actions.append(
            (
                f"Confirm move to {move['filename']}",
                lambda m=move: page.video_confirm_move(
                    video, m["video_id"], m["filename"]
                ),
            )
        )
    actions += [
        ("Properties...", lambda: page.video_properties(video)),
        ("Delete from database", lambda: page.video_delete_entry(video)),
        ("Move to Trash", lambda: page.video_trash(video)),
        ("Delete permanently", lambda: page.video_delete_file(video)),
    ]
    return videre.ContextButton("⚙", actions=actions, square=True)


def _toggle_checkbox(checkbox) -> None:
    # Click on the title toggles selection, exactly like kyuti's
    # _on_title_clicked (checkbox.setChecked(not ...)). Setting `checked` fires
    # the checkbox on_change (VideoCard._on_check), which restyles the card and
    # updates the page's global selector.
    checkbox.checked = not checkbox.checked


def _chip(name: str, value, page) -> Widget:
    # Value chip: #1976d2 underlined on #e3f2fd (kyuti:442-446). Clicking filters
    # by that value (kyuti property_value_clicked -> classifier_focus_prop_val);
    # wrapping (FlowLayout) is still gap G16. `name`/`value` are captured as
    # function parameters, so no late-binding closure bug in the caller's loop.
    box = videre.Container(
        videre.Text(str(value), color="#1976d2", underline=True),
        background_color=theme.SELECTED_BG,
        padding=videre.Padding.axis(vertical=1, horizontal=4),
    )
    if page is None:
        return box
    return _Clickable(box, on_click=lambda: page.video_filter_property(name, value))


def _attributes(
    video: VideoPattern,
    page=None,
    menu: Widget | None = None,
    checkbox: Widget | None = None,
) -> Widget:
    # Bold + underlined, black (kyuti title_label: color #000000 with <b><u>).
    title = videre.Text(
        str(video.title),
        strong=True,
        underline=True,
        wrap=videre.TextWrap.WORD,
        weight=1,
    )
    # Title is clickable (toggle selection); the weight lives on the wrapper so
    # it still fills the row next to the menu + checkbox.
    title_w: Widget = (
        _Clickable(title, on_click=lambda: _toggle_checkbox(checkbox), weight=1)
        if checkbox is not None
        else title
    )
    leading = [w for w in (menu, checkbox) if w is not None]
    if leading:
        first: Widget = videre.Row(
            [*leading, title_w], space=5, vertical_alignment=videre.Alignment.CENTER
        )
    else:
        first = title_w
    rows: list[Widget] = [first]

    if video.meta_title:
        rows.append(videre.Text(str(video.file_title), italic=True, color="#666666"))

    # Filename in a colored box, two states (kyuti video_list_item.py:195-203).
    # Monospace is a videre gap (G17). Clickable: opens the video (page.video_open)
    # and underlines on hover (kyuti _on_filename_enter/leave).
    watched = video.watched
    fname_text = videre.Text(
        str(video.filename),
        wrap=videre.TextWrap.CHAR,
        color="#a0a0a0" if watched else "#8c8cfa",
        italic=watched,
        strong=not watched,
    )
    fname_box = videre.Container(
        fname_text,
        background_color="#f8f8f8" if watched else "#fafafa",
        border=None if watched else videre.Border.all(1, "#f0f0fa"),
        padding=videre.Padding.all(2),
    )
    if page is not None:
        rows.append(
            _Clickable(
                fname_box,
                on_click=lambda: page.video_open(video),
                on_hover=lambda hovered: setattr(fname_text, "underline", hovered),
            )
        )
    else:
        rows.append(fname_box)

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
                    + [_chip(name, value, page) for value in values],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                )
            )

    return videre.Column(rows, space=3, weight=1)


class VideoCard(videre.Container):
    __wprops__ = {}
    __slots__ = ("_video", "_page", "_selected", "_hovered")
    __capture_mouse__ = True

    def __init__(
        self, video: VideoPattern, index: int = 0, page=None, selected: bool = False
    ):
        menu = _menu(video, page) if page is not None else None
        checkbox = (
            videre.Checkbox(
                checked=selected, data=video.video_id, on_change=self._on_check
            )
            if page is not None
            else None
        )
        # Per-state background + border, mirroring kyuti's VideoListItem styles
        # (no zebra striping — kyuti uses plain white for normal rows). The 6
        # states (incl. hover) live in _card_style; border radius is gap G18.
        # padding compensates the border width (padding + border == 9) so the
        # card keeps a STABLE outer size across states — a 1px→2px border on
        # hover/select would otherwise shift the layout (kyuti has this jitter).
        bg, border_width, border_color = _card_style(selected, False, video.found)
        super().__init__(
            videre.Row(
                [_thumbnail(video), _attributes(video, page, menu, checkbox)], space=12
            ),
            padding=videre.Padding.all(9 - border_width),
            background_color=bg,
            border=videre.Border.all(border_width, border_color),
        )
        self._video = video
        self._page = page
        self._selected = selected
        self._hovered = False

    def _on_check(self, checkbox) -> None:
        # Both the checkbox and the title (via _toggle_checkbox) land here: keep
        # the card's own selected state, restyle in place (kyuti restyles on
        # selection — no full reload), then update the page's global selector.
        self._selected = checkbox.checked
        self._apply_style()
        if self._page is not None:
            self._page._on_card_check(checkbox)

    def _apply_style(self) -> None:
        bg, border_width, border_color = _card_style(
            self._selected, self._hovered, self._video.found
        )
        self.background_color = bg
        self.border = videre.Border.all(border_width, border_color)
        # Keep padding + border constant so the card doesn't resize between states.
        self.padding = videre.Padding.all(9 - border_width)

    def handle_mouse_enter(self, event: MouseEvent):
        self._hovered = True
        self._apply_style()

    def handle_mouse_exit(self):
        self._hovered = False
        self._apply_style()
