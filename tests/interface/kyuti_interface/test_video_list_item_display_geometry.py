"""The video row mentions the on-screen size only when it differs.

A phone video stored 1920x1080 with a 90 degrees rotation plays -- and now
shows a thumbnail -- as 1080x1920, so the row has to say so; a plain video
keeps the shorter line it always had.
"""

import pytest
from PySide6.QtWidgets import QLabel

from pysaurus.interface.kyuti.widgets.video_list_item import VideoListItem
from tests.mocks.mock_database import MockVideoPattern

_BASE = {
    "video_id": 1,
    "filename": "/videos/test.mp4",
    "file_size": 104857600,
    "mtime": 1700000000.0,
    "duration": 3600000000,
    "duration_time_base": 1000000,
    "height": 1080,
    "width": 1920,
    "meta_title": "Test Video",
    "found": True,
    "unreadable": False,
    "watched": False,
    "with_thumbnails": False,
    "properties": {},
}


def _row_text(qtbot, prop_types, **geometry) -> str:
    video = MockVideoPattern(dict(_BASE, **geometry))
    item = VideoListItem(video, prop_types)
    qtbot.addWidget(item)
    return " ".join(label.text() for label in item.findChildren(QLabel))


def test_a_plain_video_says_nothing_more(qtbot, prop_types):
    text = _row_text(qtbot, prop_types)
    assert "1920" in text and "1080" in text
    assert "display:" not in text


def test_a_rotated_video_shows_the_swapped_size(qtbot, prop_types):
    text = _row_text(
        qtbot,
        prop_types,
        has_display_geometry=True,
        rotation=90,
        display_width=1080,
        display_height=1920,
    )
    assert "display: 1080 x 1920 ↻ 90°" in text


def test_an_anamorphic_video_shows_no_angle(qtbot, prop_types):
    text = _row_text(
        qtbot,
        prop_types,
        width=720,
        height=576,
        has_display_geometry=True,
        rotation=0,
        display_width=1024,
        display_height=576,
    )
    assert "display: 1024 x 576" in text
    assert "↻" not in text


@pytest.mark.parametrize("rotation", [90, 180, 270])
def test_every_rotation_is_spelled_out(qtbot, prop_types, rotation):
    text = _row_text(
        qtbot,
        prop_types,
        has_display_geometry=True,
        rotation=rotation,
        display_width=1080,
        display_height=1920,
    )
    assert f"↻ {rotation}°" in text
