import argparse
import inspect
import os
import shlex
import sys
import traceback
from pathlib import Path

import fire
import yaml

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.fs_utils import is_fat_filesystem
from pysaurus.core.informer import Information
from pysaurus.core.perf_counter import PerfCounter
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.algorithms.videos import Videos
from pysaurus.database.db_utils import DatabaseLoaded
from pysaurus.database.features.db_similar_videos import DbSimilarVideos
from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection
from pysaurus.dbview.view_context import ViewContext

CONFIG_FILE = ".pysaurus.yaml"


def main():
    defaults = _load_config()
    parser = argparse.ArgumentParser(description="Pysaurus CLI benchmark")
    parser.add_argument("--db", default=defaults.get("db"), help="Database name")
    parser.add_argument(
        "--home", default=defaults.get("home"), help="Home directory (default: ~)"
    )
    args, remaining = parser.parse_known_args()

    if not args.db:
        parser.error("--db is required (or set cli.db in .pysaurus.yaml)")

    db = _open_database(args.db, args.home)
    api = BenchmarkAPI(db)

    with Information():
        if remaining:
            fire.Fire(api, command=_to_fire_command(remaining))
        else:
            _repl(api)

    print("Done.")


def _load_config() -> dict:
    config_path = Path(CONFIG_FILE)
    if not config_path.is_file():
        return {}
    with open(config_path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return {}
    cli = data.get("cli")
    if not isinstance(cli, dict):
        return {}
    return cli


def _open_database(db_name: str, home: str) -> AbstractDatabase:
    home: Path = Path(home) if home else Path.home()
    db_path = home / ".Pysaurus" / "databases" / db_name
    if not db_path.is_dir():
        print(f"Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Opening database: {db_path}")

    with PerfCounter() as timer:
        db = PysaurusCollection(str(db_path))

    print(f"Opened in {timer.microseconds / 1000:.3f} ms")
    return db


def _to_fire_command(parts):
    if parts and parts[0].lower() in ("help", "h"):
        if len(parts) >= 2:
            return [parts[1], "--", "--help"]
        return ["--", "--help"]
    return parts


def _repl(api):
    print(
        "\n[CONSOLE INTERFACE]\n"
        "  exit, e, quit, q, Ctrl+C  Exit\n"
        "  help, h                   List commands\n"
        "  help <command>            Help for a command"
    )

    while True:
        calling_function = False
        try:
            line = input("[command]: ").strip()
            calling_function = True
            if not line:
                continue
            lower = line.lower()
            if lower in ("exit", "e", "quit", "q"):
                break
            parts = shlex.split(line)
            fire.Fire(api, command=_to_fire_command(parts))
        except SystemExit:
            pass
        except KeyboardInterrupt:
            if calling_function:
                print("\n\\interrupted")
            else:
                print("\n\\exit")
                break
        except Exception as exc:
            traceback.print_tb(exc.__traceback__, file=sys.stdout)
            print(r"\exception", type(exc).__name__, exc)
        print()

    print("End.")


class BenchmarkAPI:
    """Pysaurus CLI benchmark commands."""

    __slots__ = ("_db", "_view")

    def __init__(self, db: AbstractDatabase):
        self._db = db
        self._view = ViewContext()

    def backend(self):
        """Show database backend class name."""
        return type(self._db).__name__

    def name(self):
        """Show database name."""
        return self._db.get_name()

    def folders(self):
        """List database folders."""
        with PerfCounter() as t:
            result = list(self._db.get_folders())
        print(f"({t.microseconds / 1000:.3f} ms)")
        for f in result:
            print(f" {f}")
        return f"{len(result)} folder(s)"

    def update(self):
        """Update database: scan folders for new/modified videos."""
        self._db.algos.refresh()
        return "Database updated."

    def delete_entry(self, video_id: int):
        """Delete a video entry from database (keeps file on disk)."""
        with PerfCounter() as t:
            self._db.video_entry_del(video_id)
        print(f"({t.microseconds / 1000:.3f} ms)")
        return f"Deleted entry for video_id {video_id}."

    def count(self, query=""):
        """Count videos matching query flags."""
        query = str(query)
        flags = query.split() if query else []
        with PerfCounter() as t:
            result = self._db.ops.count_videos(*flags)
        print(f"({t.microseconds / 1000:.3f} ms)")
        return result

    def prop_types(self):
        """List property types."""
        with PerfCounter() as t:
            result = self._db.get_prop_types()
        print(f"({t.microseconds / 1000:.3f} ms)")
        for pt in result:
            print(f" {pt}")
        return f"{len(result)} property type(s)"

    def videos(self, limit: int = 10):
        """List videos (up to limit)."""
        with PerfCounter() as t:
            result = self._db.get_videos()
        print(f"({t.microseconds / 1000:.3f} ms) {len(result)} total")
        for v in result[:limit]:
            print(f" [{v.video_id}] {v.filename}")
        if len(result) > limit:
            print(f" ... ({len(result) - limit} more)")
        return f"{min(limit, len(result))}/{len(result)} shown"

    def video(self, video_id: int = 0):
        """Show details for a video by ID."""
        with PerfCounter() as t:
            results = self._db.get_videos(where={"video_id": video_id})
        print(f"({t.microseconds / 1000:.3f} ms)")
        if not results:
            return "Not found"
        vid = results[0]
        return str(vid)

    def tag_get(self, name: str = ""):
        """Get tag values for videos."""
        name = str(name)
        with PerfCounter() as t:
            result = self._db.videos_tag_get(name)
        print(f"({t.microseconds / 1000:.3f} ms)")
        for vid, values in list(result.items())[:10]:
            print(f" [{vid}] {values}")
        return f"{len(result)} video(s)"

    def terms(self):
        """Get video terms."""
        with PerfCounter() as t:
            result = self._db.videos_get_terms()
        print(f"({t.microseconds / 1000:.3f} ms)")
        for vid, term_list in list(result.items())[:5]:
            print(f" [{vid}] {term_list[:5]}")
        return f"{len(result)} video(s)"

    def search(self, text=""):
        """Search videos by text."""
        text = str(text)
        with PerfCounter() as t:
            self._view.set_search(text)
            result = self._db.query_videos(self._view, 0, 0)
            indices = [v.video_id for v in result.result]
        print(f"({t.microseconds / 1000:.3f} ms)")
        output = [f"{len(indices)} result(s)"] + [
            str(video_id) for video_id in indices[:10]
        ]
        if len(indices) > 10:
            output.append("...")
        return "\n".join(output)

    def groupby(
        self,
        field: str,
        is_property: bool = False,
        sorting: str = "field",
        reverse: bool = False,
        allow_singletons: bool = True,
        top: int = 10,
    ):
        """Group videos by field or property and show top groups.

        Args:
            field: Field name (e.g. audio_bit_rate) or property name (e.g. actress).
            is_property: True if field is a custom property.
            sorting: Sort groups by "field", "count", or "length".
            reverse: Reverse sort order.
            allow_singletons: Include groups with only 1 video.
            top: Number of top groups to display.
        """
        with PerfCounter() as t:
            self._view.set_grouping(
                field,
                is_property=is_property,
                sorting=sorting,
                reverse=reverse,
                allow_singletons=allow_singletons,
            )
            result = self._db.query_videos(self._view, 1, 0)
        elapsed = t.microseconds / 1000
        print(f"({elapsed:.3f} ms)")
        groups = result.result_groups
        if not groups:
            return "No grouping."
        lines = [f"{len(groups)} group(s)"]
        for g in groups[:top]:
            lines.append(f"  {g.get_printable_value()}: {g.count}")
        if len(groups) > top:
            lines.append(f"  ... ({len(groups) - top} more)")
        return "\n".join(lines)

    def sort(self, fields=""):
        """Sort videos by comma-separated fields."""
        fields = str(fields)
        sorting = fields.split(",") if fields else []
        with PerfCounter() as t:
            self._view.set_sort(sorting)
            result = self._db.query_videos(self._view, 0, 0)
            indices = [v.video_id for v in result.result]
        print(f"({t.microseconds / 1000:.3f} ms)")
        return f"{len(indices)} result(s)"

    def state(self, page_size: int = 10, page_number: int = 0):
        """Get current view state."""
        with PerfCounter() as t:
            result = self._db.query_videos(self._view, page_size, page_number)
        print(f"({t.microseconds / 1000:.3f} ms)")
        return result

    def stats(self):
        """Show database statistics."""
        with PerfCounter() as t:
            result = DatabaseLoaded(self._db)
        print(f"({t.microseconds / 1000:.3f} ms)")
        return str(result)

    def similar(self):
        """Find similar videos using image similarity search."""
        with PerfCounter() as t:
            DbSimilarVideos.find_similar_videos(self._db)
        print(f"({t.microseconds / 1000:.3f} ms)")
        return "Similar videos computed."

    def repair_fts(self):
        """Rebuild FTS5 video_text table (SQL backend only)."""
        if not isinstance(self._db, PysaurusCollection):
            return "Only available for SQL backend."
        before = self._db.db.query_one("SELECT COUNT(*) FROM video_text")[0]
        with PerfCounter() as t:
            self._db.repair_fts()
        after = self._db.db.query_one("SELECT COUNT(*) FROM video_text")[0]
        total_videos = self._db.db.query_one("SELECT COUNT(*) FROM video")[0]
        print(f"({t.microseconds / 1000:.3f} ms)")
        return f"video_text: {before} -> {after} rows (video table: {total_videos})"

    def should_update(self, limit: int = 20):
        """Dry run: show what an update would add or re-process, without modifying the DB.

        Args:
            limit: Max number of files to display per category.
        """
        with PerfCounter() as t:
            all_files = Videos.get_runtime_info_from_paths(self._db.get_folders())

        print(
            f"Scan: {len(all_files)} video(s) on disk ({t.microseconds / 1000:.3f} ms)"
        )

        # Files not in DB at all
        db_videos: dict[str, tuple] = {}
        for v in self._db.get_videos(include=["filename", "file_size", "mtime"]):
            db_videos[str(v.filename)] = (v.file_size, v.mtime)

        new_files = []
        modified_files = []
        for file_name, file_info in sorted(all_files.items()):
            key = str(file_name)
            if key not in db_videos:
                new_files.append(key)
            else:
                db_size, db_mtime = db_videos[key]
                changed = {}
                if db_size != file_info.size:
                    changed["size"] = (db_size, file_info.size)
                if db_mtime != file_info.mtime:
                    changed["mtime"] = (db_mtime, file_info.mtime)
                if changed:
                    modified_files.append((key, changed))

        # In DB but not on disk
        disk_set = set(str(f) for f in all_files)
        not_on_disk = [fn for fn in db_videos if fn not in disk_set]

        print(f"In DB: {len(db_videos)} video(s)")
        print()
        print(f"New files (not in DB):      {len(new_files)}")
        print(f"Modified (mtime/size):      {len(modified_files)}")
        print(f"In DB but not on disk:      {len(not_on_disk)}")
        print(f"Total update would process: {len(new_files) + len(modified_files)}")

        if new_files:
            print(f"\n--- New files (max {limit}) ---")
            for f in new_files[:limit]:
                print(f"  {f}")
            if len(new_files) > limit:
                print(f"  ... ({len(new_files) - limit} more)")

        if modified_files:
            print(f"\n--- Modified files (max {limit}) ---")
            for f, diffs in modified_files[:limit]:
                parts = ", ".join(
                    f"{k}: {old!r} -> {new!r}" for k, (old, new) in diffs.items()
                )
                print(f"  {f}")
                print(f"    {parts}")
            if len(modified_files) > limit:
                print(f"  ... ({len(modified_files) - limit} more)")

        return f"{len(new_files)} new, {len(modified_files)} modified"

    def fix_mtime(self, apply: bool = False, limit: int = 20):
        """Fix mtime values for videos on FAT/exFAT drives (DST drift correction).

        Re-reads mtime from disk, applies correct_mtime(), and updates the DB
        for any video whose stored mtime differs from the corrected disk value.

        Args:
            apply: Actually update the DB. Without this flag, only shows what
                   would change (dry run).
            limit: Max number of files to display.
        """
        if not isinstance(self._db, PysaurusCollection):
            return "Only available for SQL backend."

        with PerfCounter() as t:
            all_files = Videos.get_runtime_info_from_paths(self._db.get_folders())
        print(
            f"Scan: {len(all_files)} video(s) on disk ({t.microseconds / 1000:.3f} ms)"
        )

        # Build map: filename -> (video_id, db_mtime)
        db_videos: dict[str, tuple[int, float]] = {}
        for v in self._db.get_videos(
            include=["filename", "file_size", "mtime", "driver_id"]
        ):
            db_videos[str(v.filename)] = (v.video_id, v.mtime)

        # Find mtimes that need correction
        corrections: list[tuple[int, str, float, float]] = []
        for file_name, file_info in sorted(all_files.items()):
            key = str(file_name)
            if key not in db_videos:
                continue
            if not is_fat_filesystem(key):
                continue
            video_id, db_mtime = db_videos[key]
            # file_info.mtime is already corrected by the lister
            disk_mtime = file_info.mtime
            if db_mtime != disk_mtime:
                corrections.append((video_id, key, db_mtime, disk_mtime))

        if not corrections:
            return "No mtime corrections needed."

        print(f"\n{len(corrections)} video(s) with incorrect mtime on FAT/exFAT:")
        for video_id, filename, old, new in corrections[:limit]:
            diff = new - old
            print(f"  [{video_id}] {filename}")
            print(f"    {old} -> {new} (diff: {diff:+.0f}s)")
        if len(corrections) > limit:
            print(f"  ... ({len(corrections) - limit} more)")

        if not apply:
            print("\nDry run. Use fix_mtime --apply to update the database.")
            return f"{len(corrections)} correction(s) pending"

        with PerfCounter() as t:
            self._db.db.modify_many(
                "UPDATE video SET mtime = ? WHERE video_id = ?",
                ((new, vid) for vid, _, _, new in corrections),
            )
            self._db.save()
        print(f"\nUpdated {len(corrections)} mtime(s) ({t.microseconds / 1000:.3f} ms)")
        return f"{len(corrections)} correction(s) applied"

    def fix_driver_id(self, apply: bool = False, limit: int = 20):
        """Migrate driver_id from legacy integer (st_dev) to mount point path.

        Scans video folders, computes the mount point for each found file,
        and updates driver_id in the DB where the stored value differs.

        Args:
            apply: Actually update the DB. Without this flag, only shows what
                   would change (dry run).
            limit: Max number of files to display.
        """
        if not isinstance(self._db, PysaurusCollection):
            return "Only available for SQL backend."

        with PerfCounter() as t:
            all_files = Videos.get_runtime_info_from_paths(self._db.get_folders())
        print(
            f"Scan: {len(all_files)} video(s) on disk ({t.microseconds / 1000:.3f} ms)"
        )

        # Build map: standard_path -> (db_path, db_driver_id)
        # standard_path is used for matching with all_files keys,
        # db_path (with \\?\ prefix) is used in SQL WHERE clause.
        db_videos: dict[str, tuple[str, str]] = {}
        for v in self._db.get_videos(include=["filename", "driver_id"]):
            db_videos[str(v.filename)] = (v.filename.path, v.driver_id)

        # Find driver_ids that need migration
        corrections: list[tuple[str, str, str, str | None]] = []
        matched_keys: set[str] = set()
        for file_name, file_info in sorted(all_files.items()):
            key = str(file_name)
            if key not in db_videos:
                continue
            matched_keys.add(key)
            db_path, db_driver_id = db_videos[key]
            disk_driver_id = file_info.driver_id
            if db_driver_id != disk_driver_id:
                corrections.append((key, db_path, db_driver_id, disk_driver_id))

        # For not-found videos, deduce mount point from filename.
        # get_mount_point() may fail on Windows for non-existent drives
        # with Unicode paths, so fall back to drive root extraction.
        for key, (db_path, db_driver_id) in sorted(db_videos.items()):
            if key in matched_keys:
                continue
            try:
                mount_point = AbsolutePath(key).get_mount_point()
            except OSError:
                drive, _ = os.path.splitdrive(key)
                mount_point = (drive + os.sep) if drive else key
            if db_driver_id != mount_point:
                corrections.append((key, db_path, db_driver_id, mount_point))

        if not corrections:
            return "No driver_id corrections needed."

        print(f"\n{len(corrections)} video(s) with outdated driver_id:")
        for display_name, _, old, new in corrections[:limit]:
            try:
                print(f"  {display_name}")
            except UnicodeEncodeError:
                print(f"  {display_name!a}")
            print(f"    {old!r} -> {new!r}")
        if len(corrections) > limit:
            print(f"  ... ({len(corrections) - limit} more)")

        if not apply:
            print("\nDry run. Use fix_driver_id --apply to update the database.")
            return f"{len(corrections)} correction(s) pending"

        with PerfCounter() as t:
            self._db.db.modify_many(
                "UPDATE video SET driver_id = ? WHERE filename = ?",
                ((new, db_path) for _, db_path, _, new in corrections),
            )
            self._db.save()
        print(
            f"\nUpdated {len(corrections)} driver_id(s) "
            f"({t.microseconds / 1000:.3f} ms)"
        )
        return f"{len(corrections)} correction(s) applied"

    def repeat(self, command: str = "", n: int = 1):
        """Repeat a command N times and report timing."""
        command = str(command)
        parts = command.split(None, 1)
        if not parts:
            return "Usage: repeat <command> [args] <n>"
        cmd_name = parts[0]
        cmd_args_str = parts[1] if len(parts) > 1 else None
        method = getattr(self, cmd_name, None)
        if method is None or cmd_name.startswith("_"):
            return f"Unknown command: {cmd_name}"
        sig = inspect.signature(method)
        params = list(sig.parameters.values())
        if cmd_args_str:
            if len(params) == 1:
                p = params[0]
                kwargs = {p.name: p.annotation(cmd_args_str)}
            else:
                arg_list = shlex.split(cmd_args_str)
                kwargs = dict(zip([p.name for p in params], arg_list))
        else:
            kwargs = {}
        times = []
        for _ in range(n):
            with PerfCounter() as t:
                method(**kwargs)
            times.append(t.microseconds / 1000)
        mn, mx, avg = min(times), max(times), sum(times) / len(times)
        return f"{n} runs: min={mn:.3f} ms, max={mx:.3f} ms, avg={avg:.3f} ms"


if __name__ == "__main__":
    main()
