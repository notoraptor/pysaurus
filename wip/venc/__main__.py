"""
hbq — HandBrake Queue Generator using libhb
=============================================
Usage:
    python -m wip.venc --preset <preset.json> --list <videos.txt> [options]

Required arguments:
    --preset     Preset JSON file exported from HandBrake GUI
    --list       Text file with one source video path per line

Options:
    --output     Destination directory for encoded videos (default: same as source)
    --suffix     Suffix appended to the filename (e.g. " (hb)")
    --ext        Output extension override (e.g. .mkv). Inferred from preset if omitted.
    --queue      Name of the generated queue file (default: queue_output.json)
    --hb-path    Path to hb.dll if not in standard location
    --help       Show this help
"""

import argparse
import json
import sys
from pathlib import Path

from .libhb import LibHB

PRESET_FORMAT_EXTENSIONS = {"av_mp4": ".mp4", "av_mkv": ".mkv", "av_webm": ".webm"}


def load_preset(preset_path: str) -> dict:
    """Load a preset JSON file exported from HandBrake GUI."""
    path = Path(preset_path)
    if not path.exists():
        sys.exit(f"[ERROR] Preset file not found: {preset_path}")

    with open(path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            sys.exit(f"[ERROR] Preset is not valid JSON: {e}")

    preset_list = data.get("PresetList", [])
    if not preset_list:
        sys.exit("[ERROR] No presets found in the file.")

    return preset_list[0]


def detect_extension(preset: dict) -> str | None:
    """Infer the output file extension from the preset's FileFormat."""
    file_format = preset.get("FileFormat")
    if file_format:
        return PRESET_FORMAT_EXTENSIONS.get(file_format)
    return None


def read_video_list(list_path: str) -> list[str]:
    """Read the source video text file (one per line, blank lines ignored)."""
    path = Path(list_path)
    if not path.exists():
        sys.exit(f"[ERROR] Video list not found: {list_path}")

    with open(path, encoding="utf-8") as f:
        videos = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]

    if not videos:
        sys.exit("[ERROR] The video list is empty.")

    return videos


def build_destination(
    video_path: Path, output_dir: str | None, suffix: str, extension: str
) -> Path:
    """Compute the output path for a video."""
    dest_dir = Path(output_dir) if output_dir else video_path.parent
    output_name = video_path.stem + suffix + extension
    return dest_dir / output_name


def main():
    parser = argparse.ArgumentParser(
        description="Generate a HandBrake queue using libhb.", add_help=False
    )
    parser.add_argument(
        "--preset", required=True, help="Preset JSON file exported from HandBrake GUI"
    )
    parser.add_argument(
        "--list", required=True, help="Text file: one video path per line"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Destination directory for encoded videos (default: same as source)",
    )
    parser.add_argument(
        "--suffix", default="", help='Suffix appended to filename (e.g. " (hb)")'
    )
    parser.add_argument(
        "--ext",
        default=None,
        help="Output extension override (e.g. .mkv). Inferred from preset if omitted.",
    )
    parser.add_argument(
        "--queue", default="queue_output.json", help="Name of the generated queue file"
    )
    parser.add_argument(
        "--hb-path", default=None, help="Path to hb.dll if not in standard location"
    )
    parser.add_argument("--help", action="help", help="Show help")

    args = parser.parse_args()

    print("=== HandBrake Queue Generator (libhb) ===\n")

    # 1. Load preset
    print(f"[1/5] Loading preset: {args.preset}")
    preset = load_preset(args.preset)
    preset_name = preset.get("PresetName", "(unknown)")
    print(f"      Preset: {preset_name}")

    # Determine output extension
    extension = args.ext or detect_extension(preset)
    if not extension:
        sys.exit(
            "[ERROR] Could not infer output extension from preset.\n"
            "        Use --ext to specify it (e.g. --ext .mkv)."
        )
    print(f"      Output extension: {extension}")

    # 2. Read video list
    print(f"\n[2/5] Reading list: {args.list}")
    videos = read_video_list(args.list)
    print(f"      {len(videos)} video(s) found")

    # 3. Initialize libhb
    print("\n[3/5] Initializing libhb...")
    hb = LibHB(dll_path=args.hb_path)
    hb.init(verbose=0)

    # Prepare preset JSON string for libhb
    preset_json = json.dumps(preset)

    if args.output:
        Path(args.output).mkdir(parents=True, exist_ok=True)

    # 4. Scan each video and generate jobs
    print("\n[4/5] Scanning and generating jobs...")
    jobs = []
    for i, video in enumerate(videos, 1):
        video_path = Path(video)
        print(f"      [{i}/{len(videos)}] {video_path.name}")

        if not video_path.exists():
            print(f"        [WARNING] File not found, skipping: {video}")
            continue

        dest_path = build_destination(video_path, args.output, args.suffix, extension)
        if dest_path.resolve() == video_path.resolve():
            sys.exit(
                f"[ERROR] Output would overwrite source: {video}\n"
                "        Use --suffix to differentiate output files."
            )

        # Scan the source
        hb.scan(str(video_path), title_index=0)
        title_set = hb.get_title_set_json()
        title_list = title_set.get("TitleList", [])
        if not title_list:
            print(f"        [WARNING] No titles found, skipping: {video}")
            continue

        # Use the main feature or first title
        main_feature = title_set.get("MainFeature", 0)
        title_index = title_list[main_feature].get("Index", 1)

        # Apply preset to this title — HandBrake handles track selection
        job = hb.preset_job_init_json(title_index, preset_json)
        if job is None:
            print(f"        [WARNING] Preset application failed, skipping: {video}")
            continue

        # Override destination
        if "Destination" in job:
            job["Destination"]["File"] = str(dest_path)
        elif "Job" in job and "Destination" in job["Job"]:
            job["Job"]["Destination"]["File"] = str(dest_path)

        jobs.append(job)

    hb.close()

    if not jobs:
        sys.exit("[ERROR] No jobs were generated.")

    # 5. Write queue
    print(f"\n[5/5] Writing queue -> {args.queue}")
    with open(args.queue, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    print(f"\nDone: {len(jobs)} job(s) written to: {args.queue}")
    if args.output:
        print(f"  Encoded videos -> {args.output}")
    else:
        print("  Encoded videos -> same directory as source")
    print("\nNext steps:")
    print("  1. Open HandBrake")
    print("  2. File > Import Queue")
    print(f"  3. Select: {args.queue}")


if __name__ == "__main__":
    main()
