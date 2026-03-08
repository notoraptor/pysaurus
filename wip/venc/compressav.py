"""
compressav.py — Video compression using GPU-accelerated codecs via PyAV
========================================================================
Usage:
    python compressav.py --list <videos.txt> [options]
    python compressav.py [options] <video_files...>

Options:
    --codec           GPU video encoder (auto-detected if omitted)
    --quality         Video quality, lower = better (default: 24)
    --preset          Encoder preset: veryfast/.../veryslow (default: medium)
    --max-fps         Maximum framerate, 0 = no limit (default: 30)
    --copy-audio      Copy all audio tracks without re-encoding
    --audio-bitrate   Audio bitrate in kbps when encoding (default: 32)
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
import io
import sys
import time
from fractions import Fraction
from pathlib import Path

import av

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

# Codec-specific options for constant quality mode
CODEC_QUALITY_OPTIONS = {
    "hevc_qsv": {"global_quality": "{q}", "preset": "{p}", "look_ahead": "1"},
    "hevc_nvenc": {"rc": "vbr", "cq": "{q}", "preset": "{p}"},
    "hevc_amf": {"rc": "cqp", "qp_i": "{q}", "qp_p": "{q}"},
    "av1_qsv": {"global_quality": "{q}", "preset": "{p}", "look_ahead": "1"},
    "av1_nvenc": {"rc": "vbr", "cq": "{q}", "preset": "{p}"},
    "av1_amf": {"rc": "cqp", "qp_i": "{q}", "qp_p": "{q}"},
    "h264_qsv": {"global_quality": "{q}", "preset": "{p}", "look_ahead": "1"},
    "h264_nvenc": {"rc": "vbr", "cq": "{q}", "preset": "{p}"},
    "h264_amf": {"rc": "cqp", "qp_i": "{q}", "qp_p": "{q}"},
}


def main():
    parser = argparse.ArgumentParser(
        description="Compress videos using GPU-accelerated codecs.", add_help=False
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
        help="Copy all audio tracks without re-encoding "
        "(default: encode to Opus, pass through AAC)",
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
        help="Deinterlace mode (default: auto — detect and deinterlace if needed)",
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

    # Detect available GPU encoders
    print("Detecting GPU encoders...")
    available = detect_available_encoders()

    if args.list_codecs:
        if not available:
            print("  No GPU encoders found.")
        else:
            for name, desc in available:
                print(f"  {name:20s} {desc}")
        return

    if not available:
        sys.exit(
            "[ERROR] No GPU video encoder available on this machine.\n"
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
    input_path: Path,
    output_path: Path,
    codec: str,
    quality: int,
    preset: str,
    max_fps: int,
    copy_audio: bool,
    audio_bitrate: int,
    deinterlace: str,
):
    """Compress a single video file using a GPU encoder."""
    inp = av.open(str(input_path))
    out = av.open(str(output_path), "w")
    try:
        # Copy container metadata (matching HandBrake MetadataPassthru)
        out.metadata.update(inp.metadata)
        _transcode(
            inp,
            out,
            codec,
            quality,
            preset,
            max_fps,
            copy_audio,
            audio_bitrate,
            deinterlace,
        )
    finally:
        out.close()
        inp.close()


def _transcode(
    inp, out, codec, quality, preset, max_fps, copy_audio, audio_bitrate, deinterlace
):
    video_configs = []  # (in_stream, out_stream, filter_graph or None)
    audio_configs = []  # (in_stream, out_stream, resampler)
    copy_map = {}  # in_stream.index -> out_stream

    # Setup video streams
    for in_s in inp.streams.video:
        # Enable multithreaded decoding for speed
        in_s.thread_type = "AUTO"

        target_w, target_h = compute_target_size(
            in_s.codec_context.width, in_s.codec_context.height
        )
        out_s = out.add_stream(codec)
        out_s.width = target_w
        out_s.height = target_h
        out_s.pix_fmt = "nv12"

        # Framerate handling (PFR: keep original if <= max, cap otherwise)
        src_fps = float(in_s.average_rate) if in_s.average_rate else 30
        needs_deinterlace = _should_deinterlace(in_s, deinterlace)
        needs_fps_limit = bool(max_fps and src_fps > max_fps)
        out_fps = max_fps if needs_fps_limit else src_fps

        # Build filter graph (deinterlace and/or fps limiting)
        filter_graph = _build_video_filter_graph(
            in_s, needs_deinterlace, needs_fps_limit, max_fps
        )

        out_s.framerate = Fraction(out_fps).limit_denominator(10000)
        out_s.time_base = in_s.time_base
        out_s.options = get_codec_options(codec, quality, preset)
        video_configs.append((in_s, out_s, filter_graph))

        filters = []
        if needs_deinterlace:
            filters.append("yadif")
        if needs_fps_limit:
            filters.append(f"fps {src_fps:.0f}->{out_fps:.0f}")
        filter_info = f" filters=[{', '.join(filters)}]" if filters else ""
        print(
            f"  Video: {in_s.codec_context.width}x{in_s.codec_context.height}"
            f" -> {target_w}x{target_h}"
            f" [{codec} q={quality} preset={preset} {out_fps:.0f}fps]{filter_info}"
        )

    # Setup audio streams
    # Default: re-encode all audio to Opus (matching HandBrake preset2)
    for in_s in inp.streams.audio:
        src_codec = in_s.codec_context.name
        if copy_audio:
            out_s = out.add_stream_from_template(in_s)
            copy_map[in_s.index] = out_s
            print(f"  Audio track {in_s.index}: copy ({src_codec})")
        else:
            out_s = out.add_stream("libopus")
            out_s.bit_rate = audio_bitrate * 1000
            out_s.sample_rate = 48000
            out_s.layout = "stereo"
            resampler = av.AudioResampler(format="s16", layout="stereo", rate=48000)
            audio_configs.append((in_s, out_s, resampler))
            print(
                f"  Audio track {in_s.index}: {src_codec} -> Opus {audio_bitrate} kbps stereo"
            )

    # Setup subtitle streams
    for in_s in inp.streams.subtitles:
        out_s = out.add_stream_from_template(in_s)
        copy_map[in_s.index] = out_s
        print(f"  Subtitle track {in_s.index}: copy ({in_s.codec_context.name})")

    # Build lookups
    video_map = {in_s.index: (out_s, fg) for in_s, out_s, fg in video_configs}
    audio_encode_map = {
        in_s.index: (out_s, resampler) for in_s, out_s, resampler in audio_configs
    }

    # Progress tracking
    total_duration = float(inp.duration / av.time_base) if inp.duration else None
    last_pct = -1
    start_time = time.time()

    # Main demux/transcode loop
    for packet in inp.demux():
        idx = packet.stream.index

        if idx in video_map:
            out_s, filter_graph = video_map[idx]
            for frame in packet.decode():
                # Progress
                if total_duration and frame.pts is not None and frame.time_base:
                    elapsed_s = float(frame.pts * frame.time_base)
                    pct = int(elapsed_s / total_duration * 100)
                    if pct != last_pct and pct % 5 == 0:
                        speed = (
                            elapsed_s / (time.time() - start_time)
                            if time.time() > start_time
                            else 0
                        )
                        print(f"  {pct}% ({speed:.1f}x realtime)", flush=True)
                        last_pct = pct

                if filter_graph:
                    filter_graph.push(frame)
                    while True:
                        try:
                            filt_frame = filter_graph.pull()
                            _encode_video_frame(filt_frame, out_s, out)
                        except (av.error.BlockingIOError, av.error.EOFError):
                            break
                else:
                    _encode_video_frame(frame, out_s, out)

        elif idx in audio_encode_map:
            out_s, resampler = audio_encode_map[idx]
            for frame in packet.decode():
                for resampled in resampler.resample(frame):
                    for out_pkt in out_s.encode(resampled):
                        out.mux(out_pkt)

        elif idx in copy_map:
            if packet.dts is None:
                continue
            packet.stream = copy_map[idx]
            out.mux(packet)

    # Flush filter graphs
    for _, out_s, filter_graph in video_configs:
        if filter_graph:
            filter_graph.push(None)
            while True:
                try:
                    filt_frame = filter_graph.pull()
                    _encode_video_frame(filt_frame, out_s, out)
                except (av.error.EOFError, av.error.BlockingIOError):
                    break

    # Flush video encoders
    for _, out_s, _ in video_configs:
        for out_pkt in out_s.encode():
            out.mux(out_pkt)

    # Flush audio resamplers and encoders
    for _, out_s, resampler in audio_configs:
        for resampled in resampler.resample(None):
            for out_pkt in out_s.encode(resampled):
                out.mux(out_pkt)
        for out_pkt in out_s.encode():
            out.mux(out_pkt)


def _should_deinterlace(in_stream, mode):
    """Check if deinterlacing is needed based on mode and stream metadata."""
    if mode == "off":
        return False
    if mode == "on":
        return True
    # auto: detect interlaced content from stream field order
    try:
        fo = str(in_stream.codec_context.field_order).lower()
        return fo not in ("progressive", "unknown", "")
    except Exception:
        return False


def _build_video_filter_graph(in_stream, needs_deinterlace, needs_fps_limit, max_fps):
    """Build a filter graph for deinterlacing and/or fps limiting.

    Returns a configured FilterGraph, or None if no filtering is needed.
    Filters are chained: [yadif] -> [fps] (either or both may be present).
    """
    if not needs_deinterlace and not needs_fps_limit:
        return None

    graph = av.filter.Graph()
    buf_in = graph.add_buffer(
        width=in_stream.codec_context.width,
        height=in_stream.codec_context.height,
        format=av.VideoFormat(in_stream.codec_context.pix_fmt or "yuv420p"),
        time_base=in_stream.time_base,
    )
    last = buf_in

    if needs_deinterlace:
        # yadif with deint=interlaced: only deinterlace flagged frames (like decomb)
        yadif = graph.add("yadif", "mode=send_frame:parity=auto:deint=interlaced")
        last.link_to(yadif)
        last = yadif

    if needs_fps_limit:
        fps_f = graph.add("fps", f"fps={max_fps}")
        last.link_to(fps_f)
        last = fps_f

    buf_sink = graph.add("buffersink")
    last.link_to(buf_sink)
    graph.configure()
    return graph


def _encode_video_frame(frame, out_s, out):
    """Reformat if needed and encode a single video frame."""
    if (
        frame.width != out_s.width
        or frame.height != out_s.height
        or frame.format.name != out_s.pix_fmt
    ):
        frame = frame.reformat(
            width=out_s.width, height=out_s.height, format=out_s.pix_fmt
        )
    for out_pkt in out_s.encode(frame):
        out.mux(out_pkt)


def detect_available_encoders() -> list[tuple[str, str]]:
    """Detect GPU video encoders that actually work on this machine."""
    available = []
    for codec_name, description in GPU_ENCODERS:
        if is_encoder_available(codec_name):
            available.append((codec_name, description))
            print(f"  {codec_name}: available")
        else:
            print(f"  {codec_name}: not available")
    return available


def is_encoder_available(codec_name: str) -> bool:
    """Test if a GPU encoder works by encoding a single test frame."""
    for pix_fmt in ("nv12", "yuv420p"):
        try:
            buf = io.BytesIO()
            out = av.open(buf, "w", format="matroska")
            s = out.add_stream(codec_name)
            s.width = 128
            s.height = 128
            s.pix_fmt = pix_fmt
            s.time_base = Fraction(1, 30)
            s.framerate = Fraction(30, 1)
            frame = av.VideoFrame(128, 128, pix_fmt)
            frame.pts = 0
            for pkt in s.encode(frame):
                out.mux(pkt)
            for pkt in s.encode():
                out.mux(pkt)
            out.close()
            return True
        except Exception:
            continue
    return False


def compute_target_size(src_w: int, src_h: int) -> tuple[int, int]:
    """
    Compute target dimensions: 1920x1080 max for horizontal,
    1080x1920 max for vertical. Never upscales. Preserves aspect ratio.
    GPU encoders (QSV) require at least 128x128.
    """
    MIN_DIM = 128

    if src_h > src_w:
        max_w, max_h = 1080, 1920  # Vertical
    else:
        max_w, max_h = 1920, 1080  # Horizontal

    # Don't upscale
    if src_w <= max_w and src_h <= max_h:
        w, h = src_w, src_h
    else:
        scale = min(max_w / src_w, max_h / src_h)
        w = int(src_w * scale)
        h = int(src_h * scale)

    # Ensure minimum dimensions for GPU encoders
    w = max(w, MIN_DIM)
    h = max(h, MIN_DIM)

    # Codecs require even dimensions
    w -= w % 2
    h -= h % 2

    return w, h


def get_codec_options(codec_name: str, quality: int, preset: str) -> dict:
    """Get codec-specific options for constant quality encoding."""
    template = CODEC_QUALITY_OPTIONS.get(codec_name, {})
    return {k: v.format(q=quality, p=preset) for k, v in template.items()}


def collect_videos(files: list[str], list_path: str | None) -> list[str]:
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


def build_output_path(video_path: Path, output_dir: str | None, suffix: str) -> Path:
    """Compute the output path for a compressed video."""
    dest_dir = Path(output_dir) if output_dir else video_path.parent
    output_name = video_path.stem + suffix + ".mkv"
    return dest_dir / output_name


def format_size(size_bytes: int) -> str:
    """Format a file size in human-readable form."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


if __name__ == "__main__":
    main()
