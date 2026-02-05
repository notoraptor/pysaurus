"""
Create a minimal test video for testing video operations.

This video is intentionally tiny to be committed to git without bloating the repo.
Uses PyAV which is already a dependency of Pysaurus.
"""
import numpy as np
from pathlib import Path
import av


def create_minimal_test_video():
    """Create a minimal 1-second video at 64x64 resolution using PyAV."""
    # Get the fixtures directory (where this script is)
    fixtures_dir = Path(__file__).parent
    output_path = fixtures_dir / "test_video_minimal.mp4"

    print(f"Creating minimal test video at: {output_path}")

    # Create video with PyAV
    container = av.open(str(output_path), mode='w')

    # Add video stream: H.264, 64x64, 1 fps
    stream = container.add_stream('h264', rate=1)
    stream.width = 64
    stream.height = 64
    stream.pix_fmt = 'yuv420p'
    stream.options = {'crf': '51'}  # Worst quality = smallest size

    # Create 1 frame (1 second at 1 fps)
    # Solid red color
    frame = av.VideoFrame(64, 64, 'rgb24')
    frame.pts = 0

    # Fill with red color
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[:, :, 0] = 255  # Red channel
    frame.planes[0].update(arr)

    # Encode and write
    for packet in stream.encode(frame):
        container.mux(packet)

    # Flush remaining packets
    for packet in stream.encode():
        container.mux(packet)

    container.close()

    # Check file size
    file_size = output_path.stat().st_size
    print(f"✓ Video created successfully")
    print(f"  Path: {output_path}")
    print(f"  Size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
    print(f"  Resolution: 64x64")
    print(f"  Duration: ~1 second")
    print(f"  FPS: 1")
    print(f"  Codec: H.264")

    return output_path


if __name__ == '__main__':
    create_minimal_test_video()
