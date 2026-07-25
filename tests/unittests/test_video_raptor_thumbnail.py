"""Non-regression tests for the middle-of-video thumbnail capture.

A backward seek only guarantees landing on the keyframe *preceding* the target,
so the captured instant used to depend on the GOP size: two encodings of the
same content produced thumbnails seconds apart, which wrecks similarity search.
These tests encode the same 60 frames with two non-commensurable GOP sizes and
check both captures land on the same, correct frame.

Each frame is a uniform grey whose level encodes its index (frame i -> i * STEP),
so the mean pixel value of the saved thumbnail identifies the captured frame.
"""

import av
import numpy as np
import pytest
from PIL import Image

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.video_raptor.video_raptor_pyav import PythonVideoRaptor, VideoTask

FPS = 10
NB_FRAMES = 60
STEP = 4  # grey level increment per frame: frame i is filled with i * STEP
MIDDLE_FRAME = NB_FRAMES // 2  # 30, i.e. t = 3.0 s of a 6.0 s video


def _encode(path, gop: int, pts_offset: int = 0) -> None:
    """Encode NB_FRAMES uniform-grey frames, one keyframe every `gop` frames."""
    with av.open(str(path), mode="w") as container:
        stream = container.add_stream("h264", rate=FPS)
        stream.width = stream.height = 64
        stream.pix_fmt = "yuv420p"
        stream.options = {"crf": "18", "g": str(gop), "keyint_min": str(gop)}
        for i in range(NB_FRAMES):
            array = np.full((64, 64, 3), i * STEP, dtype=np.uint8)
            frame = av.VideoFrame.from_ndarray(array, format="rgb24")
            frame.pts = i + pts_offset
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


def _captured_frame_index(video_path, thumb_path) -> int:
    """Run the real capture pipeline and decode which frame it grabbed."""
    result = PythonVideoRaptor.capture(
        VideoTask(AbsolutePath(str(video_path)), thumb_path=str(thumb_path))
    )
    assert not result.error_info, result.error_info
    assert not result.error_thumbnail, result.error_thumbnail
    with Image.open(str(thumb_path)) as image:
        mean_level = np.asarray(image.convert("RGB"), dtype=np.float64).mean()
    # yuv420p round-trip shifts the level by less than one increment.
    return round(mean_level / STEP)


@pytest.mark.parametrize("extension", ["mp4", "mkv"])
def test_thumbnail_lands_on_middle_frame_whatever_the_gop(tmp_path, extension):
    """Two GOP sizes that never share a keyframe must give the same thumbnail.

    mp4 exposes stream.duration; mkv does not, which exercises the
    container.duration fallback (and its time base conversion).
    """
    indices = []
    for gop in (25, 16):  # keyframes at 0/25/50 vs 0/16/32/48
        video = tmp_path / f"gop{gop}.{extension}"
        _encode(video, gop)
        indices.append(_captured_frame_index(video, tmp_path / f"gop{gop}.jpg"))

    assert indices[0] == indices[1], (
        f"GOP-dependent capture: {indices[0]} vs {indices[1]}"
    )
    assert indices[0] == MIDDLE_FRAME


def test_thumbnail_accounts_for_stream_start_time(tmp_path):
    """A stream not starting at 0 must still be sampled at its own middle.

    With a 30 s offset, `duration // 2` used as an absolute PTS pointed before
    the first frame, so the capture returned frame 0 instead of the middle one.
    """
    video = tmp_path / "offset.mp4"
    _encode(video, gop=25, pts_offset=30 * FPS)
    assert _captured_frame_index(video, tmp_path / "offset.jpg") == MIDDLE_FRAME
