"""
Generate synthetic test videos using PyAV for database testing.

Creates thousands of small video files with varying properties:
- Different resolutions, durations, codecs
- Simple colored frames (fast to generate)
- Metadata variations
- Some identical files (duplicates)
- Some similar files (same content, different encoding)

Usage:
    python tests/generate_test_videos.py --output ./test_videos --count 10000
"""

import argparse
import random
import shutil
import time
from pathlib import Path

import av
import numpy as np


# Smaller resolutions for faster generation
RESOLUTIONS = [(160, 120), (320, 240), (320, 180), (480, 270), (640, 360)]

DURATIONS = [0.5, 1, 2]  # Very short durations

FRAMERATES = [10, 15, 24]  # Lower framerates for speed

# Use only fast codecs
CONTAINERS = [("mp4", "mpeg4"), ("avi", "mpeg4"), ("mkv", "mpeg4")]

# Categories for organizing test videos
CATEGORIES = [
    "action",
    "comedy",
    "drama",
    "documentary",
    "animation",
    "music",
    "sports",
    "nature",
    "tutorial",
    "other",
]


def generate_solid_frame(width: int, height: int, r: int, g: int, b: int) -> np.ndarray:
    """Generate a solid color frame (fastest method)."""
    frame = np.empty((height, width, 3), dtype=np.uint8)
    frame[:, :, 0] = r
    frame[:, :, 1] = g
    frame[:, :, 2] = b
    return frame


def generate_video(
    output_path: Path,
    width: int,
    height: int,
    duration: float,
    fps: int,
    codec: str,
    color_seed: int = None,
) -> dict:
    """Generate a single test video file.

    Args:
        color_seed: If provided, use this seed for color generation (for similar videos).
    """
    try:
        container = av.open(str(output_path), mode="w")

        # Add video stream with fast settings
        stream = container.add_stream(codec, rate=fps)
        stream.width = width
        stream.height = height
        stream.pix_fmt = "yuv420p"
        stream.bit_rate = 50000  # Very low bitrate

        # For mpeg4, use fast encoding options
        if codec == "mpeg4":
            stream.options = {"qscale:v": "10"}  # Lower quality = faster

        # Generate frames - use simple solid colors
        num_frames = max(1, int(duration * fps))

        # Use color_seed for reproducible colors (similar videos)
        if color_seed is not None:
            rng = random.Random(color_seed)
            base_r = rng.randint(50, 200)
            base_g = rng.randint(50, 200)
            base_b = rng.randint(50, 200)
        else:
            base_r = random.randint(50, 200)
            base_g = random.randint(50, 200)
            base_b = random.randint(50, 200)

        for i in range(num_frames):
            # Slight color variation per frame
            r = (base_r + i * 5) % 256
            g = (base_g + i * 3) % 256
            b = (base_b + i * 7) % 256

            frame_array = generate_solid_frame(width, height, r, g, b)
            frame = av.VideoFrame.from_ndarray(frame_array, format="rgb24")
            frame = frame.reformat(format="yuv420p")

            for packet in stream.encode(frame):
                container.mux(packet)

        # Flush encoder
        for packet in stream.encode():
            container.mux(packet)

        container.close()

        # Get file size
        file_size = output_path.stat().st_size

        return {"success": True, "path": str(output_path), "size": file_size}

    except Exception as e:
        if output_path.exists():
            output_path.unlink()
        return {"success": False, "path": str(output_path), "error": str(e)}


def copy_video(source_path: Path, dest_path: Path) -> dict:
    """Copy an existing video file (for identical duplicates)."""
    try:
        shutil.copy2(source_path, dest_path)
        return {
            "success": True,
            "path": str(dest_path),
            "size": dest_path.stat().st_size,
        }
    except Exception as e:
        return {"success": False, "path": str(dest_path), "error": str(e)}


def generate_test_dataset(
    output_dir: Path,
    count: int = 10000,
    seed: int = 42,
    progress_interval: int = 500,
    identical_ratio: float = 0.001,  # 0.1% identical (duplicates)
    similar_ratio: float = 0.01,  # 1% similar (same content, different encoding)
) -> dict:
    """Generate a dataset of test videos.

    Args:
        output_dir: Directory to store generated videos
        count: Total number of videos to generate
        seed: Random seed for reproducibility
        progress_interval: How often to print progress
        identical_ratio: Ratio of identical (duplicate) videos (default 0.1%)
        similar_ratio: Ratio of similar videos (default 1%)
    """
    random.seed(seed)
    np.random.seed(seed)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create category subdirectories
    for category in CATEGORIES:
        (output_dir / category).mkdir(exist_ok=True)

    # Create duplicates subdirectory
    duplicates_dir = output_dir / "_duplicates"
    duplicates_dir.mkdir(exist_ok=True)

    # Calculate counts
    num_identical = int(count * identical_ratio)
    num_similar = int(count * similar_ratio)
    num_unique = count - num_identical - num_similar

    stats = {
        "total": count,
        "unique": 0,
        "identical": 0,
        "similar": 0,
        "failed": 0,
        "total_size": 0,
        "by_resolution": {},
        "by_category": {},
        "identical_pairs": [],  # [(original, copy), ...]
        "similar_groups": [],  # [[video1, video2, ...], ...]
    }

    start_time = time.time()
    print(f"Generating {count} test videos in {output_dir}...")
    print(f"  - {num_unique} unique videos")
    print(f"  - {num_similar} similar videos (1%)")
    print(f"  - {num_identical} identical videos (0.1%)")
    print()

    generated_videos = []  # Track generated videos for duplicates/similar
    current_similar_seed = None
    similar_group = []
    videos_in_current_similar_group = 0

    # How many videos per similar group (2-4 videos share same content)
    similar_group_size = 3

    for i in range(count):
        # Determine video type
        is_identical = i >= (num_unique + num_similar) and num_identical > 0
        is_similar = (
            not is_identical and i >= num_unique and i < (num_unique + num_similar)
        )

        # Random video properties
        width, height = random.choice(RESOLUTIONS)
        duration = random.choice(DURATIONS)
        fps = random.choice(FRAMERATES)
        container_ext, codec = random.choice(CONTAINERS)
        category = random.choice(CATEGORIES)

        if is_identical:
            # Create a copy of an existing video
            if generated_videos:
                source_video = random.choice(generated_videos)
                source_path = Path(source_video["path"])

                # Put duplicate in _duplicates folder with different name
                filename = f"dup_{i:06d}_of_{source_path.stem}{source_path.suffix}"
                output_path = duplicates_dir / filename

                result = copy_video(source_path, output_path)

                if result["success"]:
                    stats["identical"] += 1
                    stats["total_size"] += result["size"]
                    stats["identical_pairs"].append(
                        (source_video["path"], str(output_path))
                    )
                else:
                    stats["failed"] += 1
            else:
                # No videos to copy yet, generate unique instead
                is_similar = False
                is_identical = False

        if is_similar:
            # Generate video with same visual content but different encoding
            # Start a new similar group every similar_group_size videos
            if videos_in_current_similar_group == 0:
                current_similar_seed = random.randint(0, 1000000)
                similar_group = []

            # Use different encoding parameters but same color seed
            # Vary resolution or container for this similar video
            if videos_in_current_similar_group > 0:
                # Use different resolution or container than previous
                width, height = random.choice(RESOLUTIONS)
                container_ext, codec = random.choice(CONTAINERS)

            filename = f"sim_{i:06d}_{width}x{height}.{container_ext}"
            output_path = output_dir / category / filename

            result = generate_video(
                output_path=output_path,
                width=width,
                height=height,
                duration=duration,
                fps=fps,
                codec=codec,
                color_seed=current_similar_seed,
            )

            if result["success"]:
                stats["similar"] += 1
                stats["total_size"] += result["size"]
                similar_group.append(str(output_path))

                res_key = f"{width}x{height}"
                stats["by_resolution"][res_key] = (
                    stats["by_resolution"].get(res_key, 0) + 1
                )
                stats["by_category"][category] = (
                    stats["by_category"].get(category, 0) + 1
                )

            videos_in_current_similar_group += 1
            if videos_in_current_similar_group >= similar_group_size:
                if len(similar_group) > 1:
                    stats["similar_groups"].append(similar_group)
                videos_in_current_similar_group = 0

        elif not is_identical:
            # Generate unique video
            filename = f"test_{i:06d}_{width}x{height}.{container_ext}"
            output_path = output_dir / category / filename

            result = generate_video(
                output_path=output_path,
                width=width,
                height=height,
                duration=duration,
                fps=fps,
                codec=codec,
            )

            if result["success"]:
                stats["unique"] += 1
                stats["total_size"] += result["size"]
                generated_videos.append(result)

                res_key = f"{width}x{height}"
                stats["by_resolution"][res_key] = (
                    stats["by_resolution"].get(res_key, 0) + 1
                )
                stats["by_category"][category] = (
                    stats["by_category"].get(category, 0) + 1
                )
            else:
                stats["failed"] += 1
                if stats["failed"] <= 5:
                    print(
                        f"  Failed: {result['path']} - {result.get('error', 'Unknown')}"
                    )

        # Progress update
        if (i + 1) % progress_interval == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            eta = (count - i - 1) / rate if rate > 0 else 0
            size_mb = stats["total_size"] / (1024 * 1024)
            print(
                f"  {i + 1:6d}/{count} ({100 * (i + 1) / count:5.1f}%) "
                f"| {rate:5.1f} vid/s | {size_mb:6.1f} MB | ETA: {eta:5.0f}s"
            )

    # Add last similar group if not empty
    if len(similar_group) > 1:
        stats["similar_groups"].append(similar_group)

    elapsed = time.time() - start_time
    stats["elapsed_seconds"] = elapsed
    stats["success"] = stats["unique"] + stats["similar"] + stats["identical"]
    stats["videos_per_second"] = count / elapsed if elapsed > 0 else 0

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic test videos for database testing"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("./test_videos"),
        help="Output directory for generated videos",
    )
    parser.add_argument(
        "--count",
        "-n",
        type=int,
        default=10000,
        help="Number of videos to generate (default: 10000)",
    )
    parser.add_argument(
        "--seed", "-s", type=int, default=42, help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    print("Test Video Generator (PyAV)")
    print("=" * 60)
    print(f"Output directory: {args.output}")
    print(f"Video count: {args.count}")
    print(f"Random seed: {args.seed}")
    print()

    stats = generate_test_dataset(
        output_dir=args.output, count=args.count, seed=args.seed
    )

    print()
    print("=" * 60)
    print("Generation complete!")
    print(f"  Total: {stats['success']} ({stats['failed']} failed)")
    print(f"    - Unique: {stats['unique']}")
    print(f"    - Similar: {stats['similar']} ({len(stats['similar_groups'])} groups)")
    print(
        f"    - Identical: {stats['identical']} ({len(stats['identical_pairs'])} pairs)"
    )
    print()
    print(f"  Total size: {stats['total_size'] / (1024 * 1024):.2f} MB")
    print(
        f"  Average size: {stats['total_size'] / max(1, stats['success']) / 1024:.1f} KB"
    )
    print(f"  Elapsed: {stats['elapsed_seconds']:.1f}s")
    print(f"  Rate: {stats['videos_per_second']:.1f} videos/s")
    print()
    print("By resolution:")
    for res, cnt in sorted(stats["by_resolution"].items()):
        print(f"  {res}: {cnt}")
    print()
    print("By category:")
    for cat, cnt in sorted(stats["by_category"].items()):
        print(f"  {cat}: {cnt}")

    # Show some examples of similar/identical
    if stats["identical_pairs"]:
        print()
        print("Identical pairs (first 3):")
        for orig, copy in stats["identical_pairs"][:3]:
            print(f"  {Path(orig).name} -> {Path(copy).name}")

    if stats["similar_groups"]:
        print()
        print("Similar groups (first 3):")
        for group in stats["similar_groups"][:3]:
            names = [Path(p).name for p in group]
            print(f"  {names}")


if __name__ == "__main__":
    main()
