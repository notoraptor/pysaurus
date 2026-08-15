"""What the interface writes next to the stored resolution.

Nothing when a player would show exactly width x height, so the common case
reads as before; the on-screen size otherwise, with the rotation only when
there is one.
"""

from types import SimpleNamespace

from pysaurus.interface.common.common import display_geometry_text


def _video(**overrides):
    data = dict(
        width=1920,
        height=1080,
        rotation=0,
        sample_aspect_ratio_num=1,
        sample_aspect_ratio_den=1,
        display_width=1920,
        display_height=1080,
    )
    data.update(overrides)
    data["has_display_geometry"] = bool(data["rotation"]) or (
        data["display_width"],
        data["display_height"],
    ) != (data["width"], data["height"])
    return SimpleNamespace(**data)


def test_square_pixels_without_rotation_say_nothing():
    assert display_geometry_text(_video()) == ""


def test_non_square_pixels_give_the_displayed_size():
    text = display_geometry_text(
        _video(
            width=720,
            height=576,
            sample_aspect_ratio_num=64,
            sample_aspect_ratio_den=45,
            display_width=1024,
            display_height=576,
        )
    )
    assert text == "display: 1024 x 576"


def test_a_rotation_is_spelled_out():
    text = display_geometry_text(
        _video(rotation=90, display_width=1080, display_height=1920)
    )
    assert text == "display: 1080 x 1920 ↻ 90°"


def test_rotation_and_aspect_ratio_combine():
    text = display_geometry_text(
        _video(
            width=720,
            height=576,
            rotation=270,
            sample_aspect_ratio_num=64,
            sample_aspect_ratio_den=45,
            display_width=576,
            display_height=1024,
        )
    )
    assert text == "display: 576 x 1024 ↻ 270°"


def test_a_video_without_the_fields_is_left_alone():
    """Older callers pass objects that know nothing of display geometry."""
    assert display_geometry_text(SimpleNamespace(has_display_geometry=None)) == ""
