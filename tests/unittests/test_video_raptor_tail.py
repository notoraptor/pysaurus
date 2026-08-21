"""The tail check: does a video's data run up to its announced duration?

The previous test seeked to the last microsecond and asked a keyframe-only
decoder for a frame, which really answered "is a keyframe left after the
announced end". That flagged healthy files whose last keyframe sits before the
announced duration -- an MPEG-TS duration is an estimate overshooting by up to
a second -- while clearing damaged tails whose index still points at data. This
one demuxes the last seconds and compares the furthest packet to the announced
duration.
"""

import av
import numpy as np

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.video_raptor.video_raptor_pyav import (
    ERROR_TRUNCATED_VIDEO,
    PythonVideoRaptor,
    VideoTask,
)

FPS = 10
NB_FRAMES = 120  # 12 s, comfortably more than the 2 s tail window


def _encode(path, faststart=False) -> None:
    options = {"movflags": "faststart"} if faststart else {}
    with av.open(str(path), mode="w", options=options) as container:
        stream = container.add_stream("h264", rate=FPS)
        stream.width = stream.height = 64
        stream.pix_fmt = "yuv420p"
        stream.options = {"crf": "30", "g": "10"}
        for i in range(NB_FRAMES):
            array = np.full((64, 64, 3), i * 2 % 256, dtype=np.uint8)
            frame = av.VideoFrame.from_ndarray(array, format="rgb24")
            frame.pts = i
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


def _capture(path):
    return PythonVideoRaptor.capture(VideoTask(AbsolutePath(str(path)), need_info=True))


def test_an_intact_video_carries_no_error(tmp_path):
    video = tmp_path / "full.mp4"
    _encode(video)
    result = _capture(video)
    assert not result.error_info, result.error_info
    assert result.info is not None
    assert list(result.info.errors) == []


def test_a_truncated_video_is_flagged(tmp_path):
    """Data cut short while the index still claims the full duration: what an
    interrupted download leaves behind (moov first, hence faststart)."""
    video = tmp_path / "full.mp4"
    _encode(video, faststart=True)
    truncated = tmp_path / "truncated.mp4"
    data = video.read_bytes()
    truncated.write_bytes(data[: int(len(data) * 0.6)])

    result = _capture(truncated)
    assert result.info is not None, result.error_info
    assert list(result.info.errors) == [ERROR_TRUNCATED_VIDEO]


def test_a_video_without_declared_duration_is_not_flagged(tmp_path):
    """An MPEG-TS declares no duration -- ffmpeg derives it from the file -- so
    a shortened one is just a valid shorter file. Nothing to flag either way."""
    video = tmp_path / "full.mp4"
    _encode(video)
    stream_copy = tmp_path / "full.ts"
    with av.open(str(video)) as src, av.open(str(stream_copy), mode="w") as dst:
        in_stream = src.streams.video[0]
        out_stream = dst.add_stream_from_template(in_stream)
        for packet in src.demux(in_stream):
            if packet.dts is None:
                continue
            packet.stream = out_stream
            dst.mux(packet)

    truncated = tmp_path / "truncated.ts"
    data = stream_copy.read_bytes()
    truncated.write_bytes(data[: int(len(data) * 0.6)])

    result = _capture(truncated)
    assert result.info is not None, result.error_info
    assert list(result.info.errors) == []
