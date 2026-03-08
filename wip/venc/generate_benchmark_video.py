"""
generate_benchmark_video.py — Generate a realistic video for compression benchmarking
======================================================================================
Usage:
    python generate_benchmark_video.py [options]

Options:
    --output    Output file path (default: benchmark_1080p_30s.mp4)
    --duration  Duration in seconds (default: 30)
    --width     Video width (default: 1920)
    --height    Video height (default: 1080)
    --fps       Framerate (default: 30)
    --help      Show this help

Generates a 1080p video with:
- Moving multi-scale wave patterns (tests gradient and detail preservation)
- Moving bright bar (tests motion estimation)
- Stereo audio chord (tests AAC passthrough in compressav.py)
- H.264 CRF 18 (high quality source, plenty of room to re-compress)
"""

import argparse
import time
from pathlib import Path

import av
import numpy as np


def main():
    parser = argparse.ArgumentParser(
        description="Generate a realistic benchmark video for compression testing."
    )
    parser.add_argument(
        "--output",
        "-o",
        default="benchmark_1080p_30s.mp4",
        help="Output file path (default: benchmark_1080p_30s.mp4)",
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        default=30,
        help="Duration in seconds (default: 30)",
    )
    parser.add_argument(
        "--width", type=int, default=1920, help="Video width (default: 1920)"
    )
    parser.add_argument(
        "--height", type=int, default=1080, help="Video height (default: 1080)"
    )
    parser.add_argument("--fps", type=int, default=30, help="Framerate (default: 30)")

    args = parser.parse_args()
    output = Path(args.output)
    print(f"Generating benchmark video: {output}")
    print(f"  {args.width}x{args.height}, {args.fps}fps, {args.duration}s")

    start = time.time()
    generate_benchmark_video(output, args.width, args.height, args.duration, args.fps)
    elapsed = time.time() - start

    size = output.stat().st_size
    print(f"\nDone in {elapsed:.1f}s")
    print(f"  File: {output}")
    print(f"  Size: {size / (1024 * 1024):.1f} MB")


def generate_benchmark_video(
    output_path: Path,
    width: int = 1920,
    height: int = 1080,
    duration: int = 30,
    fps: int = 30,
):
    """Generate a benchmark video with moving patterns and audio."""
    output_path = Path(output_path)
    container = av.open(str(output_path), mode="w")

    # Video: H.264 high quality (gives room to compress with GPU encoders)
    video_stream = container.add_stream("libx264", rate=fps)
    video_stream.width = width
    video_stream.height = height
    video_stream.pix_fmt = "yuv420p"
    video_stream.options = {"crf": "18", "preset": "fast"}

    # Audio: AAC stereo (to test AAC passthrough in compressav)
    sample_rate = 44100
    audio_stream = container.add_stream("aac", rate=sample_rate)
    audio_stream.layout = "stereo"
    audio_stream.bit_rate = 192000

    total_frames = duration * fps
    samples_per_frame = sample_rate // fps

    # Pre-compute coordinate grids (avoids re-allocation per frame)
    y = np.arange(height, dtype=np.float32).reshape(-1, 1)
    x = np.arange(width, dtype=np.float32).reshape(1, -1)
    sample_indices = np.arange(samples_per_frame, dtype=np.float32)

    print(f"  Generating {total_frames} frames...")
    for i in range(total_frames):
        t = i / fps

        # Video frame
        arr = _generate_frame(x, y, height, t)
        vframe = av.VideoFrame.from_ndarray(arr, format="rgb24")
        vframe.pts = i
        for pkt in video_stream.encode(vframe):
            container.mux(pkt)

        # Audio frame
        audio_data = _generate_audio(sample_indices, samples_per_frame, i, sample_rate)
        aframe = av.AudioFrame.from_ndarray(audio_data, format="fltp", layout="stereo")
        aframe.sample_rate = sample_rate
        aframe.pts = i * samples_per_frame
        for pkt in audio_stream.encode(aframe):
            container.mux(pkt)

        # Progress every 5 seconds of video
        if (i + 1) % (fps * 5) == 0 or i == total_frames - 1:
            pct = (i + 1) / total_frames * 100
            print(f"  {pct:.0f}%", flush=True)

    # Flush encoders
    for pkt in video_stream.encode():
        container.mux(pkt)
    for pkt in audio_stream.encode():
        container.mux(pkt)

    container.close()


def _generate_frame(x, y, height, t):
    """Generate a frame with multi-scale moving patterns.

    Creates varied spatial and temporal content:
    - Large-scale moving sine waves (tests smooth gradient coding)
    - Fine-scale moving grid (tests detail preservation)
    - Moving horizontal bright bar (tests edge coding and motion estimation)
    """
    # Large-scale moving sine waves
    r = np.sin(x / 40 + t * 3) * np.cos(y / 60 + t) * 127 + 128
    g = np.sin(y / 30 + t * 2) * np.cos(x / 50 - t * 1.5) * 127 + 128
    b = np.sin((x + y) / 50 + t * 4) * 127 + 128

    # Fine detail: moving interference pattern
    detail = np.sin(x / 8 + t * 6) * np.sin(y / 8 - t * 4) * 40
    r = r + detail
    g = g + detail * 0.7

    # Moving horizontal bright bar
    bar_y = (height / 2) + (height / 3) * np.sin(t * 1.5)
    bar_mask = np.abs(y - bar_y) < 20
    r = np.where(bar_mask, np.minimum(r + 100, 255), r)
    g = np.where(bar_mask, np.minimum(g + 100, 255), g)
    b = np.where(bar_mask, np.minimum(b + 100, 255), b)

    return np.clip(np.stack([r, g, b], axis=-1), 0, 255).astype(np.uint8)


def _generate_audio(sample_indices, num_samples, frame_idx, sample_rate):
    """Generate stereo audio with a musical chord.

    Returns a (2, num_samples) float32 array in planar format.
    Phase is continuous across frames.
    """
    phase_offset = frame_idx * num_samples
    t_samples = (sample_indices + phase_offset) / sample_rate

    # A4 + E5 chord
    left = 0.25 * np.sin(2 * np.pi * 440.0 * t_samples)
    right = 0.25 * np.sin(2 * np.pi * 659.25 * t_samples)

    return np.stack([left, right]).astype(np.float32)


if __name__ == "__main__":
    main()
