"""Storage dimensions are not display dimensions.

A player shows something else than `width` x `height` whenever the pixels are
not square (sample aspect ratio) or a display matrix asks for a rotation. Both
are captured at collect time, and the thumbnail is corrected to match, so a
720x576 anamorphic movie and a portrait phone video look on screen the way they
look in Pysaurus.

The reference orientation was pinned against ffmpeg's own autorotate output;
these tests then check the extracted `rotation` and the thumbnail agree.
"""

from fractions import Fraction

import av
import numpy as np
import pytest
from PIL import Image

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.video_raptor.video_raptor_pyav import PythonVideoRaptor, VideoTask

WIDTH, HEIGHT = 64, 32
NB_FRAMES = 20


def _encode(path, sar: Fraction, display_rotation: int) -> None:
    """Encode a landscape video whose top-left quadrant is the only bright one."""
    with av.open(str(path), mode="w") as container:
        stream = container.add_stream("h264", rate=10)
        stream.width, stream.height = WIDTH, HEIGHT
        stream.pix_fmt = "yuv420p"
        stream.sample_aspect_ratio = sar
        stream.options = {"crf": "18"}
        if display_rotation:
            stream.set_display_rotation(display_rotation)
        for i in range(NB_FRAMES):
            array = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            array[: HEIGHT // 2, : WIDTH // 2] = 255
            frame = av.VideoFrame.from_ndarray(array, format="rgb24")
            frame.pts = i
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


def _capture(tmp_path, sar=Fraction(1, 1), display_rotation=0):
    video = tmp_path / "video.mp4"
    _encode(video, sar, display_rotation)
    result = PythonVideoRaptor.capture(
        VideoTask(
            AbsolutePath(str(video)),
            need_info=True,
            thumb_path=str(tmp_path / "thumb.jpg"),
        )
    )
    assert not result.error_info, result.error_info
    assert not result.error_thumbnail, result.error_thumbnail
    with Image.open(str(tmp_path / "thumb.jpg")) as image:
        thumbnail = image.convert("RGB").copy()
    return result.info, thumbnail


def _brightest_quadrant(image: Image.Image) -> str:
    array = np.asarray(image, dtype=np.float64)
    half_h, half_w = image.height // 2, image.width // 2
    means = {
        "top-left": array[:half_h, :half_w].mean(),
        "top-right": array[:half_h, half_w:].mean(),
        "bottom-left": array[half_h:, :half_w].mean(),
        "bottom-right": array[half_h:, half_w:].mean(),
    }
    return max(means, key=means.__getitem__)


def test_square_pixels_and_no_rotation_are_the_neutral_values(tmp_path):
    info, thumbnail = _capture(tmp_path)
    assert (info.sample_aspect_ratio_num, info.sample_aspect_ratio_den) == (1, 1)
    assert info.rotation == 0
    assert (info.width, info.height) == (WIDTH, HEIGHT)
    assert thumbnail.size == (WIDTH, HEIGHT)
    assert _brightest_quadrant(thumbnail) == "top-left"


def test_an_undefined_sample_aspect_ratio_reads_as_square_pixels(tmp_path):
    """A stream carrying no SAR reads back as None, not as a fraction."""
    info, _ = _capture(tmp_path, sar=Fraction(0, 1))
    assert (info.sample_aspect_ratio_num, info.sample_aspect_ratio_den) == (1, 1)


def test_a_non_square_sample_aspect_ratio_widens_the_thumbnail(tmp_path):
    """Storage stays 64x32; the thumbnail is unsquished to the displayed 128x32."""
    info, thumbnail = _capture(tmp_path, sar=Fraction(2, 1))
    assert (info.sample_aspect_ratio_num, info.sample_aspect_ratio_den) == (2, 1)
    assert (info.width, info.height) == (WIDTH, HEIGHT)
    assert thumbnail.size == (WIDTH * 2, HEIGHT)
    assert _brightest_quadrant(thumbnail) == "top-left"


# PyAV's set_display_rotation() counts counter-clockwise, Pysaurus stores
# clockwise, hence the negation. Rotating the source clockwise by that stored
# angle moves the bright quadrant from top-left to the expected corner.
@pytest.mark.parametrize(
    "display_rotation, expected_rotation, expected_quadrant",
    [
        (0, 0, "top-left"),
        (-90, 90, "top-right"),
        (180, 180, "bottom-right"),
        (90, 270, "bottom-left"),
    ],
)
def test_rotation_is_stored_clockwise_and_applied_to_the_thumbnail(
    tmp_path, display_rotation, expected_rotation, expected_quadrant
):
    info, thumbnail = _capture(tmp_path, display_rotation=display_rotation)
    assert info.rotation == expected_rotation
    assert (info.width, info.height) == (WIDTH, HEIGHT)  # storage is never rotated
    expected_size = (
        (HEIGHT, WIDTH) if expected_rotation in (90, 270) else (WIDTH, HEIGHT)
    )
    assert thumbnail.size == expected_size
    assert _brightest_quadrant(thumbnail) == expected_quadrant


def test_sample_aspect_ratio_and_rotation_combine(tmp_path):
    """A 64x32 frame with SAR 2/1 displays as 128x32, then 32x128 once rotated."""
    info, thumbnail = _capture(tmp_path, sar=Fraction(2, 1), display_rotation=-90)
    assert (info.sample_aspect_ratio_num, info.sample_aspect_ratio_den) == (2, 1)
    assert info.rotation == 90
    assert thumbnail.size == (HEIGHT, WIDTH * 2)
    assert _brightest_quadrant(thumbnail) == "top-right"
