"""
hb_queue_gen.py — HandBrake Queue Generator
=============================================
Usage:
    python hb_queue_gen.py --template <template.json> --list <videos.txt> [options]

Required arguments:
    --template   JSON file exported from HandBrake GUI (single job, used as a model)
    --list       Text file with one source video path per line

Options:
    --output     Destination directory for encoded videos (default: same as source)
    --suffix     Suffix appended to the filename (e.g. " (hb)")
    --ext        Output extension override (e.g. .mkv) — inferred from template if not specified
    --queue      Name of the generated queue file (default: queue_output.json)
    --help       Show this help
"""

import argparse
import copy
import json
import sys
import uuid
from pathlib import Path

# HandBrake OutputFormat enum values
OUTPUT_FORMAT_EXTENSIONS = {0: ".mp4", 1: ".mkv", 2: ".webm"}


def load_template(template_path: str) -> dict:
    """Load and validate the template JSON file exported from HandBrake."""
    path = Path(template_path)
    if not path.exists():
        sys.exit(f"[ERROR] Template not found: {template_path}")

    with open(path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            sys.exit(f"[ERROR] Template is not valid JSON: {e}")

    # HandBrake exports a list of jobs
    if not isinstance(data, list) or len(data) == 0:
        sys.exit("[ERROR] Template must be a JSON list with at least one job.")

    return data[0]  # Use the first job as a model


def get_field(job: dict, *keys: str):
    """Navigate a nested dict through a sequence of keys."""
    node = job
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def set_field(job: dict, value, *keys: str) -> bool:
    """Set a field in a nested dict. Returns True on success."""
    node = job
    for key in keys[:-1]:
        if not isinstance(node, dict) or key not in node:
            return False
        node = node[key]
    if keys[-1] not in node:
        return False
    node[keys[-1]] = value
    return True


def detect_structure(job_template: dict) -> dict:
    """
    Auto-detect where source and destination fields are located
    in the template JSON structure. Handles variations between
    HandBrake versions ("Job" wrapper or not, different key names,
    direct string vs nested dict).
    """
    info = {"source": None, "destination": None}

    # HandBrake Windows may wrap in {"Job": {...}}
    root = job_template.get("Job", job_template)

    # --- Source path ---
    for source_keys in [
        ("Task", "Source"),
        ("Source",),
        ("Source", "Path"),
        ("source",),
        ("source", "path"),
    ]:
        val = get_field(root, *source_keys)
        if val and isinstance(val, str):
            info["source"] = source_keys
            break

    # --- Destination path ---
    for dest_keys in [
        ("Task", "Destination"),
        ("Destination",),
        ("Destination", "File"),
        ("destination",),
        ("destination", "file"),
    ]:
        val = get_field(root, *dest_keys)
        if val and isinstance(val, str):
            info["destination"] = dest_keys
            break

    if not info["source"]:
        sys.exit(
            "[ERROR] Cannot find source path in the template.\n"
            "        Make sure the JSON was exported from HandBrake GUI."
        )
    if not info["destination"]:
        sys.exit("[ERROR] Cannot find destination path in the template.")

    return info


def detect_extension(job_template: dict) -> str | None:
    """Infer the output file extension from the template's OutputFormat field."""
    root = job_template.get("Job", job_template)
    for node in [root.get("Task", {}), root]:
        output_format = node.get("OutputFormat", node.get("outputFormat"))
        if output_format is not None:
            return OUTPUT_FORMAT_EXTENSIONS.get(output_format)
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


def generate_queue(
    job_template: dict,
    videos: list[str],
    output_dir: str | None,
    suffix: str,
    structure: dict,
    extension: str,
) -> list[dict]:
    """
    Generate the list of jobs for the HandBrake queue.
    For each video, clone the template and update source + destination.
    The output path is computed from --output, --suffix and the extension.
    """
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    jobs = []
    has_job_wrapper = "Job" in job_template

    for video in videos:
        video_path = Path(video)
        dest_dir = Path(output_dir) if output_dir else video_path.parent
        output_name = video_path.stem + suffix + extension
        output_path = dest_dir / output_name

        if output_path.resolve() == video_path.resolve():
            sys.exit(
                f"[ERROR] Output would overwrite source: {video}\n"
                "        Use --suffix to differentiate output files."
            )

        job = copy.deepcopy(job_template)
        root = job["Job"] if has_job_wrapper else job

        # Update source
        src_ok = set_field(root, str(video_path), *structure["source"])
        # Update destination
        dst_ok = set_field(root, str(output_path), *structure["destination"])

        if not src_ok or not dst_ok:
            print(f"  [WARNING] Could not update paths for: {video}")
            continue

        # Update ScannedSourcePath if present
        if "ScannedSourcePath" in root:
            root["ScannedSourcePath"] = str(video_path)
        # Remove cached source metadata (HandBrake re-scans on import)
        root.pop("SourceTitleInfo", None)
        root.pop("Statistics", None)
        # Clean source-specific fields inside the task
        task = get_field(root, *structure["source"][:-1]) or root
        for audio_track in task.get("AudioTracks", []):
            audio_track.pop("ScannedTrack", None)
            audio_track.pop("TrackName", None)
        task.pop("ChapterNames", None)
        task.pop("MetaData", None)
        # Generate a unique TaskId
        if "TaskId" in root:
            root["TaskId"] = str(uuid.uuid4())

        jobs.append(job)

    return jobs


def main():
    parser = argparse.ArgumentParser(
        description="Generate a HandBrake queue from a template JSON.", add_help=False
    )
    parser.add_argument(
        "--template",
        required=True,
        help="Template JSON file (1 job exported from HandBrake GUI)",
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
        help="Output extension override (e.g. .mkv). Inferred from template if omitted.",
    )
    parser.add_argument(
        "--queue", default="queue_output.json", help="Name of the generated queue file"
    )
    parser.add_argument("--help", action="help", help="Show help")

    args = parser.parse_args()

    print("=== HandBrake Queue Generator ===\n")

    # 1. Load the template
    print(f"[1/4] Loading template: {args.template}")
    job_template = load_template(args.template)

    # 2. Detect JSON structure
    print("[2/4] Detecting template structure...")
    structure = detect_structure(job_template)
    print(f"      Source field      : {' > '.join(structure['source'])}")
    print(f"      Destination field : {' > '.join(structure['destination'])}")

    # Determine output extension
    extension = args.ext or detect_extension(job_template)
    if not extension:
        sys.exit(
            "[ERROR] Could not infer output extension from template.\n"
            "        Use --ext to specify it (e.g. --ext .mkv)."
        )
    print(f"      Output extension  : {extension}")

    # 3. Read the video list
    print(f"\n[3/4] Reading list: {args.list}")
    videos = read_video_list(args.list)
    print(f"      {len(videos)} video(s) found")

    # 4. Generate the queue
    print(f"\n[4/4] Generating queue -> {args.queue}")
    jobs = generate_queue(
        job_template, videos, args.output, args.suffix, structure, extension
    )

    with open(args.queue, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    print(f"\nDone: {len(jobs)} job(s) written to: {args.queue}")
    if args.output:
        print(f"  Encoded videos -> {args.output}")
    else:
        print("  Encoded videos -> same directory as source")
    print("\nNext steps:")
    print("  1. Open HandBrake")
    print("  2. File > Import Queue (or Queue > Import Queue)")
    print(f"  3. Select: {args.queue}")


if __name__ == "__main__":
    main()
