"""
Create a minimal test video for testing video operations.

Videos are intentionally tiny to be committed to git without bloating the repo.
Uses PyAV which is already a dependency of Pysaurus.

Usage:
    python create_test_video.py              # 1-second video (test_video_minimal.mp4)
    python create_test_video.py 15           # 15-second video (test_video_15s.mp4)
    python create_test_video.py 30 out.mp4   # 30-second video at custom path
"""

import argparse
from pathlib import Path

import av
import numpy as np


def create_test_video(duration_seconds=1, output_path=None):
    """Create a minimal test video at 64x64 resolution using PyAV.

    Args:
        duration_seconds: Duration in seconds (number of frames at 1 fps).
        output_path: Output file path. If None, generates a default name
            in the same directory as this script.

    Returns:
        The Path of the created video file.
    """
    if output_path is None:
        fixtures_dir = Path(__file__).parent
        if duration_seconds == 1:
            output_path = fixtures_dir / "test_video_minimal.mp4"
        else:
            output_path = fixtures_dir / f"test_video_{duration_seconds}s.mp4"
    output_path = Path(output_path)

    container = av.open(str(output_path), mode="w")

    # H.264, 64x64, 1 fps, worst quality for smallest size
    stream = container.add_stream("h264", rate=1)
    stream.width = 64
    stream.height = 64
    stream.pix_fmt = "yuv420p"
    stream.options = {"crf": "51"}

    for i in range(duration_seconds):
        frame = av.VideoFrame(64, 64, "rgb24")
        frame.pts = i
        arr = np.zeros((64, 64, 3), dtype=np.uint8)
        arr[:, :, i % 3] = 255  # Cycle through R, G, B
        frame.planes[0].update(arr)
        for packet in stream.encode(frame):
            container.mux(packet)

    for packet in stream.encode():
        container.mux(packet)

    container.close()

    file_size = output_path.stat().st_size
    print(f"Created {output_path}")
    print(f"  Size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
    print(f"  Duration: {duration_seconds}s, 64x64, 1 fps, H.264")

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a minimal test video.")
    parser.add_argument(
        "duration",
        nargs="?",
        type=int,
        default=1,
        help="Duration in seconds (default: 1)",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Output file path (default: auto-generated)",
    )
    args = parser.parse_args()
    create_test_video(args.duration, args.output)
