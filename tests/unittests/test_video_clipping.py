import base64
import os
import shutil
from pathlib import Path

import pytest

from pysaurus.core.core_exceptions import ZeroLengthError
from pysaurus.core.video_clipping import VideoClipping

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
TEST_VIDEO = FIXTURES_DIR / "test_video_15s.mp4"


@pytest.fixture()
def video_in_tmp(tmp_path):
    """Copy the 15-second test video into a temporary directory."""
    dest = tmp_path / "video.mp4"
    shutil.copy2(TEST_VIDEO, dest)
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield str(dest)
    os.chdir(original_cwd)
    # Clean up any generated clip files
    for f in tmp_path.glob("*.mp4"):
        if f != dest:
            f.unlink(missing_ok=True)


class TestVideoClipValidation:
    """Tests for argument validation (no video file needed)."""

    def test_time_start_must_be_non_negative_int(self):
        with pytest.raises(AssertionError):
            VideoClipping.video_clip("video.mp4", time_start=-1)

    def test_time_start_must_be_int(self):
        with pytest.raises(AssertionError):
            VideoClipping.video_clip("video.mp4", time_start=1.5)

    def test_clip_seconds_must_be_positive_int(self):
        with pytest.raises(AssertionError):
            VideoClipping.video_clip("video.mp4", clip_seconds=0)

    def test_clip_seconds_must_be_int(self):
        with pytest.raises(AssertionError):
            VideoClipping.video_clip("video.mp4", clip_seconds=2.5)


class TestVideoClip:
    """Tests for VideoClipping.video_clip with a real video file."""

    def test_normal_clip(self, video_in_tmp):
        output = VideoClipping.video_clip(
            video_in_tmp, time_start=2, clip_seconds=5, unique_id="test"
        )
        assert output == "test_2_5.mp4"
        assert os.path.isfile(output)

    def test_normal_clip_produces_valid_video(self, video_in_tmp):
        import av

        output = VideoClipping.video_clip(
            video_in_tmp, time_start=0, clip_seconds=5, unique_id="test"
        )
        container = av.open(output)
        stream = container.streams.video[0]
        duration = float(stream.duration * stream.time_base)
        assert duration == pytest.approx(5.0, abs=0.5)
        container.close()

    def test_time_end_clamped_to_duration(self, video_in_tmp):
        import av

        # time_start=10, clip_seconds=10 => time_end=20 > 15, clamped to 15
        output = VideoClipping.video_clip(
            video_in_tmp, time_start=10, clip_seconds=10, unique_id="test"
        )
        assert os.path.isfile(output)
        container = av.open(output)
        stream = container.streams.video[0]
        duration = float(stream.duration * stream.time_base)
        assert duration == pytest.approx(5.0, abs=0.5)
        container.close()

    def test_time_start_beyond_duration_raises_zero_length(self, video_in_tmp):
        # time_start=20 > duration=15, both clamped to 15 => ZeroLengthError
        with pytest.raises(ZeroLengthError):
            VideoClipping.video_clip(
                video_in_tmp, time_start=20, clip_seconds=5, unique_id="test"
            )

    def test_time_start_at_duration_raises_zero_length(self, video_in_tmp):
        # time_start=15 == duration, time_end=25 clamped to 15 => ZeroLengthError
        with pytest.raises(ZeroLengthError):
            VideoClipping.video_clip(
                video_in_tmp, time_start=15, clip_seconds=10, unique_id="test"
            )

    def test_output_name_with_unique_id(self, video_in_tmp):
        output = VideoClipping.video_clip(
            video_in_tmp, time_start=0, clip_seconds=3, unique_id="myid"
        )
        assert output == "myid_0_3.mp4"

    def test_output_name_without_unique_id(self, video_in_tmp):
        from pysaurus.core.modules import FNV64

        expected_id = FNV64.hash(os.path.abspath(video_in_tmp))
        output = VideoClipping.video_clip(video_in_tmp, time_start=0, clip_seconds=3)
        assert output == f"{expected_id}_0_3.mp4"

    def test_default_clip_seconds(self, video_in_tmp):
        output = VideoClipping.video_clip(video_in_tmp, time_start=0, unique_id="test")
        # Default clip_seconds=10, video is 15s, so clip should be ~10s
        assert output == "test_0_10.mp4"
        assert os.path.isfile(output)


class TestVideoClipToBase64:
    """Tests for VideoClipping.video_clip_to_base64 with a real video file."""

    def test_returns_base64_bytes(self, video_in_tmp):
        result = VideoClipping.video_clip_to_base64(
            video_in_tmp, time_start=0, clip_seconds=3, unique_id="b64test"
        )
        assert isinstance(result, bytes)
        # Verify it's valid base64 by decoding it
        decoded = base64.b64decode(result)
        assert len(decoded) > 0

    def test_output_file_is_deleted(self, video_in_tmp):
        VideoClipping.video_clip_to_base64(
            video_in_tmp, time_start=0, clip_seconds=3, unique_id="cleanup"
        )
        assert not os.path.exists("cleanup_0_3.mp4")

    def test_base64_matches_clip_content(self, video_in_tmp):
        # First generate the clip to get its content
        output = VideoClipping.video_clip(
            video_in_tmp, time_start=0, clip_seconds=3, unique_id="compare"
        )
        with open(output, "rb") as f:
            expected_content = f.read()
        os.unlink(output)

        # Now use video_clip_to_base64 with same parameters
        result = VideoClipping.video_clip_to_base64(
            video_in_tmp, time_start=0, clip_seconds=3, unique_id="compare"
        )
        assert result == base64.b64encode(expected_content)
