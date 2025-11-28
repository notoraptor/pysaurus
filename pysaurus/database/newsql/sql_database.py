"""
NewSqlDatabase - SQL-based video database implementation.

This implementation stores videos as JSON blobs in SQLite, providing:
- Unified storage (videos, thumbnails, index in one file)
- Atomic transactions
- Better performance for large collections
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from pysaurus.core.profiling import Profiler

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1


class SqlDatabase:
    """Low-level SQL database operations."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        connection: sqlite3.Connection | None = None,
    ):
        """
        Initialize SqlDatabase.

        Args:
            db_path: Path to the SQLite database file. Can be None if connection is provided.
            connection: Optional existing connection (e.g., for in-memory databases).
        """
        self.db_path = Path(db_path) if db_path else None
        self._conn: sqlite3.Connection | None = connection
        if connection is not None:
            connection.row_factory = sqlite3.Row

    @classmethod
    def from_memory_copy(cls, source_db_path: Path | str) -> "SqlDatabase":
        """
        Create an in-memory copy of an existing database.

        This is useful for tests where you want to modify the database
        without affecting the original file.
        """
        source_db_path = Path(source_db_path)
        # Create in-memory connection
        mem_conn = sqlite3.connect(":memory:", isolation_level=None)
        mem_conn.row_factory = sqlite3.Row

        # Copy source database to memory
        with sqlite3.connect(source_db_path) as source_conn:
            source_conn.backup(mem_conn)

        # Enable foreign keys (WAL mode not needed for in-memory)
        mem_conn.execute("PRAGMA foreign_keys = ON")

        return cls(db_path=None, connection=mem_conn)

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            if self.db_path is None:
                raise ValueError("No database path or connection provided")
            self._conn = sqlite3.connect(self.db_path, isolation_level=None)
            self._conn.row_factory = sqlite3.Row
            # Enable foreign keys and WAL mode for better performance
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.execute("PRAGMA journal_mode = WAL")
        return self._conn

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def executemany(self, sql: str, params_list: Iterable[tuple]) -> sqlite3.Cursor:
        return self.conn.executemany(sql, params_list)

    def begin(self):
        self.conn.execute("BEGIN")

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def init_schema(self):
        """Initialize database schema from schema.sql file."""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        self.conn.executescript(schema_sql)

        # Set initial config if empty
        version = self.get_config("version")
        if version is None:
            self.set_config("version", SCHEMA_VERSION)
            self.set_config("date", 0)

    # =========================================================================
    # Config operations
    # =========================================================================

    def get_config(self, key: str) -> Any:
        row = self.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        return json.loads(row["value"])

    def set_config(self, key: str, value: Any):
        json_value = json.dumps(value)
        self.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, json_value),
        )

    # =========================================================================
    # Folders operations
    # =========================================================================

    def get_folders(self) -> list[str]:
        rows = self.execute("SELECT path FROM folders").fetchall()
        return [row["path"] for row in rows]

    def set_folders(self, folders: Iterable[str]):
        self.execute("DELETE FROM folders")
        self.executemany(
            "INSERT INTO folders (path) VALUES (?)", [(f,) for f in folders]
        )

    def add_folder(self, path: str):
        self.execute("INSERT OR IGNORE INTO folders (path) VALUES (?)", (path,))

    def remove_folder(self, path: str):
        self.execute("DELETE FROM folders WHERE path = ?", (path,))

    # =========================================================================
    # PropType operations
    # =========================================================================

    def get_prop_types(self) -> list[dict]:
        rows = self.execute(
            "SELECT name, definition, multiple FROM prop_types"
        ).fetchall()
        return [
            {
                "name": row["name"],
                "definition": json.loads(row["definition"])
                if row["definition"] is not None
                else None,
                "multiple": bool(row["multiple"]),
            }
            for row in rows
        ]

    def get_prop_type(self, name: str) -> dict | None:
        row = self.execute(
            "SELECT name, definition, multiple FROM prop_types WHERE name = ?", (name,)
        ).fetchone()
        if row is None:
            return None
        return {
            "name": row["name"],
            "definition": json.loads(row["definition"])
            if row["definition"] is not None
            else None,
            "multiple": bool(row["multiple"]),
        }

    def set_prop_type(self, name: str, definition: Any, multiple: bool):
        # Always JSON-encode definition, even for falsy values like "", 0, False
        json_def = json.dumps(definition)
        self.execute(
            "INSERT OR REPLACE INTO prop_types (name, definition, multiple) VALUES (?, ?, ?)",
            (name, json_def, int(multiple)),
        )

    def delete_prop_type(self, name: str):
        self.execute("DELETE FROM prop_types WHERE name = ?", (name,))

    def rename_prop_type(self, old_name: str, new_name: str):
        self.execute(
            "UPDATE prop_types SET name = ? WHERE name = ?", (new_name, old_name)
        )

    # =========================================================================
    # Video operations
    # =========================================================================

    def get_video_count(self) -> int:
        row = self.execute("SELECT COUNT(*) as cnt FROM videos").fetchone()
        return row["cnt"]

    def get_all_videos(self) -> list[dict]:
        rows = self.execute("SELECT video_id, filename, data FROM videos").fetchall()
        return [
            {
                "video_id": row["video_id"],
                "filename": row["filename"],
                "data": json.loads(row["data"]),
            }
            for row in rows
        ]

    def get_video_by_id(self, video_id: int) -> dict | None:
        row = self.execute(
            "SELECT video_id, filename, data FROM videos WHERE video_id = ?",
            (video_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "video_id": row["video_id"],
            "filename": row["filename"],
            "data": json.loads(row["data"]),
        }

    def get_video_by_filename(self, filename: str) -> dict | None:
        row = self.execute(
            "SELECT video_id, filename, data FROM videos WHERE filename = ?",
            (filename,),
        ).fetchone()
        if row is None:
            return None
        return {
            "video_id": row["video_id"],
            "filename": row["filename"],
            "data": json.loads(row["data"]),
        }

    def get_video_filenames(self) -> list[str]:
        rows = self.execute("SELECT filename FROM videos").fetchall()
        return [row["filename"] for row in rows]

    def insert_video(self, video_id: int, filename: str, data: dict):
        json_data = json.dumps(data)
        self.execute(
            "INSERT INTO videos (video_id, filename, data) VALUES (?, ?, ?)",
            (video_id, filename, json_data),
        )

    def update_video(self, video_id: int, data: dict):
        json_data = json.dumps(data)
        self.execute(
            "UPDATE videos SET data = ? WHERE video_id = ?", (json_data, video_id)
        )

    def update_video_filename(self, video_id: int, new_filename: str, data: dict):
        json_data = json.dumps(data)
        self.execute(
            "UPDATE videos SET filename = ?, data = ? WHERE video_id = ?",
            (new_filename, json_data, video_id),
        )

    def update_videos_batch(self, updates: list[tuple[int, dict, str]]):
        """
        Batch update multiple videos in a single transaction.

        Args:
            updates: List of (video_id, data_dict, filename) tuples
        """
        if not updates:
            return

        self.begin()
        try:
            params = [
                (json.dumps(data), video_id) for video_id, data, filename in updates
            ]
            self.executemany("UPDATE videos SET data = ? WHERE video_id = ?", params)
            self.commit()
        except Exception:
            self.rollback()
            raise

    def delete_video(self, video_id: int):
        self.execute("DELETE FROM videos WHERE video_id = ?", (video_id,))

    def get_next_video_id(self) -> int:
        row = self.execute(
            "SELECT COALESCE(MAX(video_id), -1) + 1 as next_id FROM videos"
        ).fetchone()
        return row["next_id"]

    # =========================================================================
    # Thumbnail operations
    # =========================================================================

    def has_thumbnail(self, filename: str) -> bool:
        row = self.execute(
            "SELECT 1 FROM thumbnails WHERE filename = ?", (filename,)
        ).fetchone()
        return row is not None

    def get_thumbnail(self, filename: str) -> bytes | None:
        row = self.execute(
            "SELECT blob FROM thumbnails WHERE filename = ?", (filename,)
        ).fetchone()
        return row["blob"] if row else None

    def set_thumbnail(self, filename: str, blob: bytes):
        self.execute(
            "INSERT OR REPLACE INTO thumbnails (filename, blob) VALUES (?, ?)",
            (filename, blob),
        )

    def delete_thumbnail(self, filename: str):
        self.execute("DELETE FROM thumbnails WHERE filename = ?", (filename,))

    def rename_thumbnail(self, old_filename: str, new_filename: str):
        self.execute(
            "UPDATE thumbnails SET filename = ? WHERE filename = ?",
            (new_filename, old_filename),
        )

    def get_thumbnail_count(self) -> int:
        row = self.execute("SELECT COUNT(*) as cnt FROM thumbnails").fetchone()
        return row["cnt"]

    # =========================================================================
    # Search index operations
    # =========================================================================

    def clear_search_index(self):
        self.execute("DELETE FROM search_terms")
        self.execute("DELETE FROM video_flags")

    def add_search_terms(self, filename: str, terms: Iterable[str]):
        self.executemany(
            "INSERT OR IGNORE INTO search_terms (term, filename) VALUES (?, ?)",
            [(term, filename) for term in terms],
        )

    def remove_search_terms(self, filename: str):
        self.execute("DELETE FROM search_terms WHERE filename = ?", (filename,))

    def set_video_flags(self, filename: str, flags: dict[str, bool]):
        # Remove old flags
        self.execute("DELETE FROM video_flags WHERE filename = ?", (filename,))
        # Insert new flags
        self.executemany(
            "INSERT INTO video_flags (filename, flag, value) VALUES (?, ?, ?)",
            [(filename, flag, int(value)) for flag, value in flags.items()],
        )

    def remove_video_flags(self, filename: str):
        self.execute("DELETE FROM video_flags WHERE filename = ?", (filename,))

    def query_terms_and(self, terms: list[str]) -> set[str]:
        """Return filenames containing ALL terms."""
        if not terms:
            return set()

        # Build query with subqueries for each term
        placeholders = ",".join("?" * len(terms))
        sql = f"""
            SELECT filename FROM search_terms
            WHERE term IN ({placeholders})
            GROUP BY filename
            HAVING COUNT(DISTINCT term) = ?
        """
        rows = self.execute(sql, (*terms, len(terms))).fetchall()
        return {row["filename"] for row in rows}

    def query_terms_or(self, terms: list[str]) -> set[str]:
        """Return filenames containing ANY term."""
        if not terms:
            return set()

        placeholders = ",".join("?" * len(terms))
        sql = (
            f"SELECT DISTINCT filename FROM search_terms WHERE term IN ({placeholders})"
        )
        rows = self.execute(sql, terms).fetchall()
        return {row["filename"] for row in rows}

    def query_flags(self, flags: dict[str, bool]) -> set[str]:
        """Return filenames matching ALL flag conditions."""
        if not flags:
            # Return all filenames
            rows = self.execute("SELECT DISTINCT filename FROM video_flags").fetchall()
            return {row["filename"] for row in rows}

        conditions = []
        params = []
        for flag, value in flags.items():
            conditions.append("(flag = ? AND value = ?)")
            params.extend([flag, int(value)])

        sql = f"""
            SELECT filename FROM video_flags
            WHERE {" OR ".join(conditions)}
            GROUP BY filename
            HAVING COUNT(*) = ?
        """
        params.append(len(flags))
        rows = self.execute(sql, params).fetchall()
        return {row["filename"] for row in rows}

    @Profiler.profile_method()
    def rebuild_search_index(
        self, videos: Iterable[dict], flags_extractor, terms_extractor
    ):
        """Rebuild the entire search index from video data."""
        self.clear_search_index()

        self.begin()
        try:
            for video in videos:
                filename = video["filename"]
                terms = terms_extractor(video)
                flags = flags_extractor(video)

                self.add_search_terms(filename, terms)
                self.set_video_flags(filename, flags)

            self.commit()
        except Exception:
            self.rollback()
            raise
