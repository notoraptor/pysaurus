import argparse
import inspect
import shlex
import sys
import traceback
from pathlib import Path

import fire

from pysaurus.core.perf_counter import PerfCounter
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.db_utils import DatabaseLoaded
from pysaurus.database.jsdb.json_database import JsonDatabase
from saurus.sql.pysaurus_collection import PysaurusCollection


def main():
    parser = argparse.ArgumentParser(description="Pysaurus CLI benchmark")
    parser.add_argument(
        "--backend",
        choices=["json", "sql"],
        required=True,
        help="Database backend (json or sql)",
    )
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--home", default=None, help="Home directory (default: ~)")
    args, remaining = parser.parse_known_args()

    db = _open_database(args.db, args.backend, args.home)
    api = BenchmarkAPI(db)

    if remaining:
        fire.Fire(api, command=remaining)
    else:
        _repl(api)

    print("Done.")


def _open_database(db_name: str, backend: str, home: str) -> AbstractDatabase:
    home = Path(home) if home else Path.home()
    db_path = home / ".Pysaurus" / "databases" / db_name
    if not db_path.is_dir():
        print(f"Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    backend_label = backend.upper()
    print(f"Opening {backend_label} database: {db_path}")

    with PerfCounter() as timer:
        if backend == "json":
            db = JsonDatabase(str(db_path))
        else:
            db = PysaurusCollection(str(db_path))

    print(f"Opened in {timer.microseconds / 1000:.3f} ms")
    return db


def _repl(api):
    print(
        "\n[CONSOLE INTERFACE] "
        '("exit", "e", "quit", "q" or Ctrl+C to exit, "help" or "h" for help)'
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
            if lower == "help" or lower == "h":
                fire.Fire(api, command=["--", "--help"])
                continue
            parts = shlex.split(line)
            if len(parts) >= 2 and parts[0].lower() in ("help", "h"):
                fire.Fire(api, command=[parts[1], "--", "--help"])
                continue
            fire.Fire(api, command=parts)
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

    __slots__ = ("_db",)

    def __init__(self, db: AbstractDatabase):
        self._db = db

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
        return "\n".join(f" {k}: {val}" for k, val in vid.to_dict().items())

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
            self._db.provider.set_search(text)
            indices = self._db.provider.get_view_indices()
        print(f"({t.microseconds / 1000:.3f} ms)")
        return f"{len(indices)} result(s)"

    def sort(self, fields=""):
        """Sort videos by comma-separated fields."""
        fields = str(fields)
        sorting = fields.split(",") if fields else []
        with PerfCounter() as t:
            self._db.provider.set_sort(sorting)
            indices = self._db.provider.get_view_indices()
        print(f"({t.microseconds / 1000:.3f} ms)")
        return f"{len(indices)} result(s)"

    def state(self, page_size: int = 10, page_number: int = 0):
        """Get current provider state."""
        with PerfCounter() as t:
            result = self._db.provider.get_current_state(page_size, page_number)
        print(f"({t.microseconds / 1000:.3f} ms)")
        return result

    def stats(self):
        """Show database statistics."""
        with PerfCounter() as t:
            result = DatabaseLoaded(self._db)
        print(f"({t.microseconds / 1000:.3f} ms)")
        return str(result)

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
