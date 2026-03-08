"""
compressff.py — Video compression using FFmpeg subprocess (via imageio-ffmpeg)
==============================================================================
Usage:
    python compressff.py --list <videos.txt> [options]
    python compressff.py [options] <video_files...>

Options:
    --codec           GPU video encoder (auto-detected if omitted)
    --quality         Video quality, lower = better (default: 24)
    --preset          Encoder preset: veryfast/.../veryslow (default: medium)
    --max-fps         Maximum framerate, 0 = no limit (default: 30)
    --copy-audio      Copy all audio tracks without re-encoding
    --audio-bitrate   Audio bitrate in kbps when encoding (default: 64)
    --deinterlace     Deinterlace mode: auto/on/off (default: auto)
    --output          Output directory (default: same as source)
    --suffix          Filename suffix (default: " (compressed)")
    --list            Text file with one video path per line
    --list-codecs     List available GPU encoders and exit
    --help            Show this help

Audio behavior (default):
    All audio tracks are re-encoded to Opus at --audio-bitrate kbps stereo.
    Use --copy-audio to copy all audio tracks without re-encoding.

Opus bitrate guide (stereo):
    24 kbps  — speech only (podcasts, VoIP)
    32 kbps  — speech OK, music degraded (screencasts, surveillance)
    48 kbps  — decent speech + simple music (web video, low bandwidth)
    64 kbps  — good general quality, ~MP3 128 (personal video collections)
    96 kbps  — very good, hard to tell from original for most listeners
    128 kbps — near-transparent (music-heavy content, audiophiles)
    160+ kbps — transparent (archival, production)
"""

import argparse
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from imageio_ffmpeg import get_ffmpeg_exe

# GPU encoder candidates, ordered by preference
GPU_ENCODERS = [
    ("hevc_qsv", "H.265 (Intel QSV)"),
    ("hevc_nvenc", "H.265 (NVIDIA NVENC)"),
    ("hevc_amf", "H.265 (AMD AMF)"),
    ("av1_qsv", "AV1 (Intel QSV)"),
    ("av1_nvenc", "AV1 (NVIDIA NVENC)"),
    ("av1_amf", "AV1 (AMD AMF)"),
    ("h264_qsv", "H.264 (Intel QSV)"),
    ("h264_nvenc", "H.264 (NVIDIA NVENC)"),
    ("h264_amf", "H.264 (AMD AMF)"),
]

# Codec-specific CLI options for constant quality mode
# All options use :v:0 qualifier to avoid conflicts with audio encoder init
CODEC_CLI_OPTIONS = {
    "hevc_qsv": [
        "-global_quality:v:0",
        "{q}",
        "-preset:v:0",
        "{p}",
        "-look_ahead:v:0",
        "1",
    ],
    "hevc_nvenc": ["-rc:v:0", "vbr", "-cq:v:0", "{q}", "-preset:v:0", "{p}"],
    "hevc_amf": ["-rc:v:0", "cqp", "-qp_i:v:0", "{q}", "-qp_p:v:0", "{q}"],
    "av1_qsv": [
        "-global_quality:v:0",
        "{q}",
        "-preset:v:0",
        "{p}",
        "-look_ahead:v:0",
        "1",
    ],
    "av1_nvenc": ["-rc:v:0", "vbr", "-cq:v:0", "{q}", "-preset:v:0", "{p}"],
    "av1_amf": ["-rc:v:0", "cqp", "-qp_i:v:0", "{q}", "-qp_p:v:0", "{q}"],
    "h264_qsv": [
        "-global_quality:v:0",
        "{q}",
        "-preset:v:0",
        "{p}",
        "-look_ahead:v:0",
        "1",
    ],
    "h264_nvenc": ["-rc:v:0", "vbr", "-cq:v:0", "{q}", "-preset:v:0", "{p}"],
    "h264_amf": ["-rc:v:0", "cqp", "-qp_i:v:0", "{q}", "-qp_p:v:0", "{q}"],
}


@dataclass
class VideoInfo:
    width: int
    height: int
    fps: float
    duration: float
    video_codec: str
    audio_codec: str | None
    is_interlaced: bool


def main():
    parser = argparse.ArgumentParser(
        description="Compress videos using GPU-accelerated FFmpeg.", add_help=False
    )
    parser.add_argument("files", nargs="*", help="Video files to compress")
    parser.add_argument(
        "--list", default=None, help="Text file: one video path per line"
    )
    parser.add_argument(
        "--codec", default=None, help="GPU encoder name (e.g. hevc_qsv)"
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=24,
        help="Video quality, lower=better (default: 24)",
    )
    parser.add_argument(
        "--preset",
        default="medium",
        help="Encoder preset: veryfast/faster/fast/medium/slow/veryslow (default: medium)",
    )
    parser.add_argument(
        "--max-fps",
        type=int,
        default=30,
        help="Maximum framerate, 0 = no limit (default: 30)",
    )
    parser.add_argument(
        "--copy-audio",
        action="store_true",
        help="Copy all audio tracks without re-encoding",
    )
    parser.add_argument(
        "--audio-bitrate",
        type=int,
        default=64,
        help="Audio bitrate in kbps (default: 64)",
    )
    parser.add_argument(
        "--deinterlace",
        choices=["auto", "on", "off"],
        default="auto",
        help="Deinterlace mode (default: auto)",
    )
    parser.add_argument(
        "--output", default=None, help="Output directory (default: same as source)"
    )
    parser.add_argument(
        "--suffix",
        default=" (compressed)",
        help='Filename suffix (default: " (compressed)")',
    )
    parser.add_argument(
        "--list-codecs",
        action="store_true",
        help="List available GPU encoders and exit",
    )
    parser.add_argument("--help", action="help", help="Show help")

    args = parser.parse_args()

    ffmpeg = get_ffmpeg_exe()
    print(f"FFmpeg: {ffmpeg}")

    # Detect available GPU encoders
    print("Detecting GPU encoders...")
    available = detect_available_encoders(ffmpeg)

    if args.list_codecs:
        if not available:
            print("  No GPU encoders found.")
        else:
            for name, desc in available:
                print(f"  {name:20s} {desc}")
        return

    if not available:
        sys.exit(
            "[ERROR] No GPU video encoder available.\n"
            "        A GPU with hardware encoding support is required."
        )

    # Select codec
    if args.codec:
        available_names = [name for name, _ in available]
        if args.codec not in available_names:
            sys.exit(
                f"[ERROR] Encoder '{args.codec}' is not available.\n"
                f"        Available: {', '.join(available_names)}"
            )
        codec = args.codec
    else:
        codec = available[0][0]

    codec_desc = next((d for n, d in available if n == codec), codec)
    print(f"  Using: {codec} ({codec_desc})\n")

    # Collect video files
    videos = collect_videos(args.files, args.list)
    if not videos:
        sys.exit(
            "[ERROR] No video files specified. Use --list or pass files as arguments."
        )

    print(f"{len(videos)} video(s) to compress\n")

    if args.output:
        Path(args.output).mkdir(parents=True, exist_ok=True)

    # Process each video
    success = 0
    for i, video in enumerate(videos, 1):
        video_path = Path(video)
        print(f"[{i}/{len(videos)}] {video_path.name}")

        if not video_path.exists():
            print(f"  [SKIP] File not found: {video}")
            continue

        output_path = build_output_path(video_path, args.output, args.suffix)
        if output_path.resolve() == video_path.resolve():
            print("  [SKIP] Output would overwrite source. Use --suffix or --output.")
            continue

        try:
            compress_video(
                ffmpeg,
                video_path,
                output_path,
                codec,
                args.quality,
                args.preset,
                args.max_fps,
                args.copy_audio,
                args.audio_bitrate,
                args.deinterlace,
            )
            src_size = video_path.stat().st_size
            dst_size = output_path.stat().st_size
            ratio = dst_size / src_size * 100 if src_size > 0 else 0
            print(
                f"  Done: {format_size(src_size)} -> {format_size(dst_size)} ({ratio:.0f}%)"
            )
            success += 1
        except Exception as e:
            print(f"  [ERROR] {e}")
            if output_path.exists():
                output_path.unlink()

    print(f"\n{success}/{len(videos)} video(s) compressed successfully.")


def compress_video(
    ffmpeg,
    input_path,
    output_path,
    codec,
    quality,
    preset,
    max_fps,
    copy_audio,
    audio_bitrate,
    deinterlace,
):
    """Compress a single video file using FFmpeg subprocess."""
    info = probe_video(ffmpeg, input_path)

    # Build video filters
    vf_filters = _build_video_filters(info, max_fps, deinterlace)

    # Compute target dimensions for logging
    target_w, target_h = _compute_target_size(info.width, info.height)
    out_fps = max_fps if (max_fps and info.fps > max_fps) else info.fps

    filters = []
    if deinterlace == "on" or (deinterlace == "auto" and info.is_interlaced):
        filters.append("yadif")
    if max_fps and info.fps > max_fps:
        filters.append(f"fps {info.fps:.0f}->{out_fps:.0f}")
    filter_info = f" filters=[{', '.join(filters)}]" if filters else ""

    print(
        f"  Video: {info.width}x{info.height} -> {target_w}x{target_h}"
        f" [{codec} q={quality} preset={preset} {out_fps:.0f}fps]{filter_info}"
    )
    if copy_audio:
        print(f"  Audio: copy ({info.audio_codec or 'unknown'})")
    else:
        print(
            f"  Audio: {info.audio_codec or 'unknown'} -> Opus {audio_bitrate} kbps stereo"
        )

    # Build and run command
    cmd = _build_ffmpeg_command(
        ffmpeg,
        input_path,
        output_path,
        vf_filters,
        codec,
        quality,
        preset,
        copy_audio,
        audio_bitrate,
    )
    _run_with_progress(cmd, info.duration)


def _build_video_filters(info, max_fps, deinterlace):
    """Build the -vf filter chain."""
    filters = []

    # Deinterlace (before scale for better quality)
    if deinterlace == "on" or (deinterlace == "auto" and info.is_interlaced):
        filters.append("yadif=mode=send_frame:parity=auto:deint=interlaced")

    # Orientation-aware scale (no upscale, preserve aspect ratio, even dimensions)
    if info.height > info.width:
        max_w, max_h = 1080, 1920  # Vertical
    else:
        max_w, max_h = 1920, 1080  # Horizontal
    filters.append(
        f"scale=w='min(iw\\,{max_w})':h='min(ih\\,{max_h})':"
        f"force_original_aspect_ratio=decrease:force_divisible_by=2"
    )

    # FPS limit (PFR: only cap, don't increase)
    if max_fps and info.fps > max_fps:
        filters.append(f"fps={max_fps}")

    # GPU encoders expect nv12 pixel format
    filters.append("format=nv12")

    return ",".join(filters)


def _build_ffmpeg_command(
    ffmpeg,
    input_path,
    output_path,
    vf_filters,
    codec,
    quality,
    preset,
    copy_audio,
    audio_bitrate,
):
    """Build the full ffmpeg command."""
    cmd = [
        ffmpeg,
        "-y",
        "-nostdin",
        "-hide_banner",
        "-i",
        str(input_path),
        "-map",
        "0:v",
        "-map",
        "0:a?",
        "-map",
        "0:s?",
        "-c:v:0",
        codec,
    ]

    # Codec-specific quality options (with explicit stream index)
    cmd.extend(get_codec_options(codec, quality, preset))

    # Video filters
    cmd.extend(["-vf", vf_filters])

    # Audio (explicit stream indices required: QSV + libopus conflict otherwise)
    if copy_audio:
        cmd.extend(["-c:a", "copy"])
    else:
        cmd.extend(
            [
                "-c:a:0",
                "libopus",
                "-b:a:0",
                str(audio_bitrate * 1000),
                "-vbr:a:0",
                "on",
                "-ar:a:0",
                "48000",
                "-ac:a:0",
                "2",
            ]
        )

    # Subtitles: copy
    cmd.extend(["-c:s", "copy"])

    # Metadata passthrough
    cmd.extend(["-map_metadata", "0"])

    # Progress output on stdout
    cmd.extend(["-progress", "pipe:1", "-nostats"])

    cmd.append(str(output_path))
    return cmd


def _run_with_progress(cmd, total_duration):
    """Run ffmpeg subprocess and display progress."""
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # Read stderr in background to prevent deadlock
    stderr_lines = []

    def _read_stderr():
        for line in process.stderr:
            stderr_lines.append(line)

    t = threading.Thread(target=_read_stderr, daemon=True)
    t.start()

    last_pct = -1
    start_time = time.time()

    for line in process.stdout:
        if line.startswith("out_time_us="):
            try:
                time_us = int(line.split("=")[1])
            except (ValueError, IndexError):
                continue
            if time_us < 0:
                continue
            elapsed_s = time_us / 1_000_000
            if total_duration > 0:
                pct = int(elapsed_s / total_duration * 100)
                if pct != last_pct and pct % 5 == 0:
                    wall = time.time() - start_time
                    speed = elapsed_s / wall if wall > 0 else 0
                    print(f"  {pct}% ({speed:.1f}x realtime)", flush=True)
                    last_pct = pct

    process.wait()
    t.join(timeout=5)

    if process.returncode != 0:
        error = "".join(stderr_lines[-20:])
        raise RuntimeError(f"FFmpeg exited with code {process.returncode}:\n{error}")


def _compute_target_size(src_w, src_h):
    """Compute target dimensions for logging (mirrors the scale filter logic)."""
    if src_h > src_w:
        max_w, max_h = 1080, 1920
    else:
        max_w, max_h = 1920, 1080

    if src_w <= max_w and src_h <= max_h:
        w, h = src_w, src_h
    else:
        scale = min(max_w / src_w, max_h / src_h)
        w = int(src_w * scale)
        h = int(src_h * scale)

    w -= w % 2
    h -= h % 2
    return w, h


def probe_video(ffmpeg, input_path):
    """Probe video file using ffmpeg -i to extract stream info."""
    r = subprocess.run(
        [ffmpeg, "-i", str(input_path), "-hide_banner"], capture_output=True, text=True
    )
    stderr = r.stderr

    # Duration: 00:05:30.00
    dur_match = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", stderr)
    duration = 0.0
    if dur_match:
        h, m, s = dur_match.groups()
        duration = int(h) * 3600 + int(m) * 60 + float(s)

    # Video stream — match the full line so fps/interlace info is included
    video_line_match = re.search(r"Stream.*Video:.*", stderr)
    width, height, video_codec = 0, 0, ""
    video_line = ""
    if video_line_match:
        video_line = video_line_match.group(0)
        codec_match = re.search(r"Video:\s*(\w+)", video_line)
        if codec_match:
            video_codec = codec_match.group(1)
        res_match = re.search(r"(\d{2,5})x(\d{2,5})", video_line)
        if res_match:
            width = int(res_match.group(1))
            height = int(res_match.group(2))

    # FPS: try "X fps" first, fall back to "X tbr"
    fps = 30.0
    fps_match = re.search(r"([\d.]+)\s*fps", video_line)
    if not fps_match:
        fps_match = re.search(r"([\d.]+)\s*tbr", video_line)
    if fps_match:
        fps = float(fps_match.group(1))

    # Interlaced: "top first" or "bottom first" in video stream line
    is_interlaced = bool(re.search(r"top first|bottom first", video_line, re.I))

    # Audio stream
    audio_match = re.search(r"Stream.*Audio:\s*(\w+)", stderr)
    audio_codec = audio_match.group(1) if audio_match else None

    return VideoInfo(
        width=width,
        height=height,
        fps=fps,
        duration=duration,
        video_codec=video_codec,
        audio_codec=audio_codec,
        is_interlaced=is_interlaced,
    )


def detect_available_encoders(ffmpeg):
    """Detect GPU video encoders that work on this machine."""
    available = []
    for codec_name, description in GPU_ENCODERS:
        if is_encoder_available(ffmpeg, codec_name):
            available.append((codec_name, description))
            print(f"  {codec_name}: available")
        else:
            print(f"  {codec_name}: not available")
    return available


def is_encoder_available(ffmpeg, codec_name):
    """Test if a GPU encoder works by encoding a single test frame."""
    try:
        r = subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-nostdin",
                "-f",
                "lavfi",
                "-i",
                "nullsrc=s=128x128:d=0.1",
                "-c:v",
                codec_name,
                "-frames:v",
                "1",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            timeout=10,
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_codec_options(codec_name, quality, preset):
    """Get codec-specific CLI args for constant quality encoding."""
    template = CODEC_CLI_OPTIONS.get(codec_name, [])
    return [arg.format(q=quality, p=preset) for arg in template]


def collect_videos(files, list_path):
    """Collect video file paths from arguments and/or a list file."""
    videos = list(files) if files else []
    if list_path:
        path = Path(list_path)
        if not path.exists():
            sys.exit(f"[ERROR] Video list not found: {list_path}")
        with open(path, encoding="utf-8") as f:
            videos.extend(
                line.strip() for line in f if line.strip() and not line.startswith("#")
            )
    return videos


def build_output_path(video_path, output_dir, suffix):
    """Compute the output path for a compressed video."""
    dest_dir = Path(output_dir) if output_dir else video_path.parent
    output_name = video_path.stem + suffix + ".mkv"
    return dest_dir / output_name


def format_size(size_bytes):
    """Format a file size in human-readable form."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


if __name__ == "__main__":
    main()
