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

from pysaurus.interface.videroid.widgets.video_card import VideoCard
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
        assert "NOT FOUND" in _texts(VideoCard(_video(found=False), 0))

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
        assert _find(card, videre.ContextButton)  # per-video actions menu
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
