"""Branch coverage for video_card states, using MockVideoPattern.

Each test asserts the ACTUAL widget tree built by VideoCard.__init__ (status
texts, specs line, thumbnail fallback, menu/checkbox), walking the tree
statically — no render needed, since the children are set at construction.

MockVideoPattern.readable is True unless `unreadable` is set, and its `thumbnail`
is always b"" — so a full "readable" dict is needed to exercise the specs block,
and a subclass is needed for an invalid (non-empty) thumbnail.
"""

from unittest.mock import Mock

import videre
from videre.core.events import MouseButton

from pysaurus.interface.videroid.widgets.video_card import (
    VideoCard,
    _card_style,
    _Clickable,
)
from tests.interface.videroid_interface._widget_tree import find as _find
from tests.interface.videroid_interface._widget_tree import texts as _texts
from tests.mocks.mock_database import MockVideoPattern

_READABLE = {
    "filename": "/v.mp4",
    "file_size": 1,
    "video_id": 1,
    "mtime": 0.0,
    "size": "1 MB",
    "container_format": "mp4",
    "video_codec": "h264",
    "audio_codec": "aac",
    "byte_rate": 1000,
    "length": "1:00",
    "width": 1920,
    "height": 1080,
    "frame_rate": 30,
    "bit_depth": 8,
    "sample_rate": 48000,
    "channels": 2,
    "audio_bit_rate_formatted": "128k",
}


def _video(**overrides):
    return MockVideoPattern(dict(_READABLE, **overrides))


class _BadThumbVideo(MockVideoPattern):
    @property
    def thumbnail(self):
        return b"not-an-image"  # non-empty but invalid -> PIL open fails


class TestVideoCardStates:
    def test_readable_video_shows_specs(self):
        texts = _texts(VideoCard(_video(found=True), 0))
        assert any("h264" in t and "aac" in t for t in texts)  # codec line
        assert any("1920 x 1080" in t for t in texts)  # resolution line

    def test_not_found_status(self):
        card = VideoCard(_video(found=False), 0)
        assert "NOT FOUND" in _texts(card)
        # Not-found rows get the pale-yellow background (matches kyuti #fffde7).
        assert card.background_color == videre.Gradient.parse("#fffde7")
        # Exact status color (kyuti #cc0000), not videre's named red.
        nf = next(t for t in _find(card, videre.Text) if t.text == "NOT FOUND")
        assert nf.color == videre.parse_color("#cc0000")

    def test_title_is_bold_and_underlined(self):
        # Only the title is both bold and underlined (kyuti title <b><u>); chips
        # are underlined-not-bold, the filename bold-not-underlined.
        card = VideoCard(_video(found=True), 0)
        both = [t for t in _find(card, videre.Text) if t.underline and t.strong]
        assert both

    def test_unreadable_status_skips_specs(self):
        texts = _texts(VideoCard(_video(found=True, unreadable=True), 0))
        assert "Unreadable" in texts
        assert not any("h264" in t for t in texts)  # readable=False -> no specs

    def test_meta_title_shows_file_title(self):
        video = _video(found=True, meta_title="M")
        assert str(video.file_title) in _texts(VideoCard(video, 0))

    def test_errors_shown(self):
        texts = _texts(VideoCard(_video(found=True, errors=["boom"]), 0))
        assert any("boom" in t for t in texts)

    def test_similarity_shown(self):
        card = VideoCard(_video(found=True, similarity_id=3, similarity=42), 0)
        assert "Similarity: 42" in _texts(card)
        sim = next(t for t in _find(card, videre.Text) if "Similarity" in t.text)
        assert sim.color == videre.parse_color("#0066cc")  # kyuti similarity color

    def test_invalid_thumbnail_falls_back_to_picture(self):
        card = VideoCard(_BadThumbVideo(dict(_READABLE, found=True)), 0)
        # Non-empty but invalid data -> the except branch builds a Picture, NOT
        # the "(no thumbnail)" placeholder.
        assert "(no thumbnail)" not in _texts(card)
        assert _find(card, videre.Picture)

    def test_no_thumbnail_shows_placeholder(self):
        card = VideoCard(_video(found=True), 0)  # MockVideoPattern.thumbnail == b""
        assert "(no thumbnail)" in _texts(card)
        assert not _find(card, videre.Picture)

    def test_with_page_builds_menu_and_checked_checkbox(self):
        card = VideoCard(_video(found=True), 0, page=Mock(), selected=True)
        menu = _find(card, videre.ContextButton)[0]  # per-video actions menu
        assert "Properties..." in [label for label, _ in menu.actions]
        boxes = _find(card, videre.Checkbox)
        assert len(boxes) == 1
        assert boxes[0].checked is True and boxes[0].data == 1  # selected, right id

    def test_no_page_has_no_menu_or_checkbox(self):
        card = VideoCard(_video(found=True), 0)  # page=None
        assert not _find(card, videre.ContextButton)
        assert not _find(card, videre.Checkbox)

    def test_watched_status(self):
        texts = _texts(VideoCard(_video(found=True, watched=True), 0))
        assert "Watched" in texts


class TestVideoCardInteraction:
    """The 6 hover states + the local (window-free) half of the click wiring
    (mirrors kyuti VideoListItem). The click path itself needs a mounted window
    (get_window) and is covered in test_videos_page_full::TestCardInteraction."""

    def test_card_style_six_states(self):
        # Exact kyuti VideoListItem._apply_style table (video_list_item.py:543).
        assert _card_style(True, True, True) == ("#d0e8fc", 2, "#1565c0")
        assert _card_style(True, False, True) == ("#e3f2fd", 2, "#1976d2")
        assert _card_style(False, True, False) == ("#ffecb3", 2, "#ff9800")
        assert _card_style(False, False, False) == ("#fffde7", 1, "#ffe082")
        assert _card_style(False, True, True) == ("#f5f9ff", 1, "#90caf9")
        assert _card_style(False, False, True) == ("#ffffff", 1, "#dddddd")

    def test_hover_restyles_found(self):
        card = VideoCard(_video(found=True), 0)
        card.handle_mouse_enter(None)
        assert card.background_color == videre.Gradient.parse("#f5f9ff")
        card.handle_mouse_exit()
        assert card.background_color == videre.Gradient.parse("#ffffff")

    def test_hover_restyles_not_found(self):
        card = VideoCard(_video(found=False), 0)
        card.handle_mouse_enter(None)
        assert card.background_color == videre.Gradient.parse("#ffecb3")
        card.handle_mouse_exit()
        assert card.background_color == videre.Gradient.parse("#fffde7")

    def test_selected_hover_state(self):
        card = VideoCard(_video(found=True), 0, selected=True)
        assert card.background_color == videre.Gradient.parse("#e3f2fd")
        card.handle_mouse_enter(None)
        assert card.background_color == videre.Gradient.parse("#d0e8fc")

    def test_on_check_selects_restyles_and_notifies(self):
        page = Mock()
        card = VideoCard(_video(found=True), 0, page=page)
        card._on_check(Mock(checked=True, data=1))
        assert card._selected is True
        assert card.background_color == videre.Gradient.parse("#e3f2fd")  # selected
        page._on_card_check.assert_called_once()

    def test_filename_hover_underlines(self):
        # Non-watched filename is #8c8cfa; hover toggles the inner Text underline.
        card = VideoCard(_video(found=True), 0, page=Mock())
        fname = next(
            t
            for t in _find(card, videre.Text)
            if t.color == videre.parse_color("#8c8cfa")
        )
        assert fname.underline is False
        clickable = next(
            c for c in _find(card, _Clickable) if fname in _find(c, videre.Text)
        )
        clickable.handle_mouse_enter(None)
        assert fname.underline is True
        clickable.handle_mouse_exit()
        assert fname.underline is False

    def test_clickable_ignores_non_left_click(self):
        calls = []
        clickable = _Clickable(videre.Text("x"), on_click=lambda: calls.append(1))
        assert clickable.handle_click(MouseButton.BUTTON_RIGHT) is clickable
        assert calls == []

    def test_padding_compensates_border_width(self):
        # not-found border is 1px (padding 8); hover bumps it to 2px (padding 7),
        # so padding + border == 9 and the card's outer size never jitters.
        card = VideoCard(_video(found=False), 0)
        assert card.padding.top == 8
        card.handle_mouse_enter(None)
        assert card.padding.top == 7

    def test_menu_has_similarity_actions_when_matched(self):
        # A video with a real similarity match (>= 0) gets Dismiss + Reset.
        card = VideoCard(_video(found=True, similarity_id=3), 0, page=Mock())
        menu = _find(card, videre.ContextButton)[0]
        labels = [label for label, _ in menu.actions]
        assert "Dismiss similarity" in labels and "Reset similarity" in labels

    def test_menu_confirm_move_only_when_video_has_moves(self):
        # A missing video with candidate destinations gets one flat item each.
        moves = [{"video_id": 9, "filename": "/found/dst.mp4"}]
        card = VideoCard(_video(found=False, moves=moves), 0, page=Mock())
        labels = [label for label, _ in _find(card, videre.ContextButton)[0].actions]
        assert "Confirm move to /found/dst.mp4" in labels
        plain = VideoCard(_video(found=True), 0, page=Mock())
        labels = [label for label, _ in _find(plain, videre.ContextButton)[0].actions]
        assert not any(lbl.startswith("Confirm move to") for lbl in labels)

    def test_menu_generalize_items_follow_similarity_grouping(self):
        def labels(video, grouped):
            page = Mock()
            page.grouped_by_similarity.return_value = grouped
            menu = _find(VideoCard(video, 0, page=page), videre.ContextButton)[0]
            return [label for label, _ in menu.actions]

        with_meta = _video(found=True, meta_title="M")
        got = labels(with_meta, True)
        assert "Generalize meta title into property..." in got
        assert "Generalize file title into property..." in got
        # No meta title -> only the file-title item.
        got = labels(_video(found=True), True)
        assert "Generalize meta title into property..." not in got
        assert "Generalize file title into property..." in got
        # Not grouped by similarity -> no generalize items at all.
        assert not any(lbl.startswith("Generalize") for lbl in labels(with_meta, False))
