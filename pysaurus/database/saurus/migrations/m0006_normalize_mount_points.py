"""Migration to version 6: normalize the mount point of every stored path.

Windows spells a drive either way (``C:\\`` or ``c:\\``) and AbsolutePath keeps
what it was given, so one file could be stored under two spellings that never
compare equal -- splitting the "disk" grouping and making indexed videos look
unknown to the folder scan. Paths now enter the database with a normalized
mount point (``fs_utils.normalize_mount_point``); this brings existing rows in
line.

Only the drive or UNC prefix is touched, never the rest of the path: the
STORED ``extension``/``file_title`` columns derive from the basename, so titles
are unaffected. No-op on POSIX, where there is no prefix to normalize -- and on
a Windows database already spelled the conventional way, since a drive folds to
uppercase.

Two spellings of one file would collide on UNIQUE(filename), and merging them
needs the application, so the migration refuses to run rather than pick a
winner. This never reaches a new user: a fresh database is created directly at
LATEST_VERSION, so m0006 only ever runs on databases predating the rule -- ours,
which `pysaurus.scripts.migrate_databases` reports to be free of conflicts.

Data-only: no schema change, hence no table rebuild.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pysaurus.application.exceptions import MountPointCaseConflict
from pysaurus.core.fs_utils import normalize_mount_point

if TYPE_CHECKING:
    from skullite import Skullite


def _check_no_conflict(connection) -> None:
    """Refuse the migration if two filenames differ only by their mount point.

    Runs before any write, so a refusal leaves the database exactly as it was.
    `pysaurus.scripts.migrate_databases` lists every conflict at once.
    """
    seen: dict[str, str] = {}
    for row in connection.query_all("SELECT filename FROM video"):
        filename = row["filename"]
        normalized = normalize_mount_point(filename)
        if normalized in seen:
            raise MountPointCaseConflict(seen[normalized], filename)
        seen[normalized] = filename


def _normalize_column(connection, table: str, column: str) -> None:
    """Rewrite every value of `column` whose mount point is not normalized."""
    rows = connection.query_all(f"SELECT DISTINCT {column} FROM {table}")
    changes = [
        (new, old)
        for old in (row[column] for row in rows)
        if old and (new := normalize_mount_point(old)) != old
    ]
    if changes:
        connection.modify(
            f"UPDATE {table} SET {column} = ? WHERE {column} = ?", changes, many=True
        )


def _deduplicate_sources(connection) -> None:
    """Drop sources that another source already covers once normalized."""
    seen: set[str] = set()
    for row in connection.query_all("SELECT source FROM collection_source"):
        source = row["source"]
        normalized = normalize_mount_point(source)
        if normalized in seen:
            connection.modify(
                "DELETE FROM collection_source WHERE source = ?", [source]
            )
        else:
            seen.add(normalized)


def migrate(db: Skullite) -> None:
    with db.connect() as connection:
        _check_no_conflict(connection)
        _normalize_column(connection, "video", "filename")
        _normalize_column(connection, "video", "driver_id")
        _deduplicate_sources(connection)
        _normalize_column(connection, "collection_source", "source")
