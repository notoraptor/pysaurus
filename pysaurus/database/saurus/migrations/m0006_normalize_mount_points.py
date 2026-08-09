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

Conflicting rows (two spellings of one file, which the very bug being fixed
used to create) are reported and left alone rather than merged or refused:
merging picks a winner the user never chose, and refusing would make the
database unopenable for good, since the only way to merge them is from inside
the application. They stay exactly as they are today.

Data-only: no schema change, hence no table rebuild.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pysaurus.core.fs_utils import normalize_mount_point

if TYPE_CHECKING:
    from skullite import Skullite

logger = logging.getLogger(__name__)


def find_filename_conflicts(connection) -> list[list[str]]:
    """Groups of stored filenames that differ only by their mount point."""
    grouped: dict[str, list[str]] = {}
    for row in connection.query_all("SELECT filename FROM video"):
        grouped.setdefault(normalize_mount_point(row["filename"]), []).append(
            row["filename"]
        )
    return [sorted(names) for names in grouped.values() if len(names) > 1]


def _report_conflicts(conflicts: list[list[str]]) -> None:
    logger.warning(
        "%d file(s) are stored under several spellings of their mount point. "
        "Those rows are left untouched, so the database still opens and behaves "
        "as before, but they keep the duplicate entries you may already see. "
        "This migration runs once and will not revisit them:\n%s",
        len(conflicts),
        "\n".join("  " + " <-> ".join(names) for names in conflicts),
    )


def _normalize_column(connection, table: str, column: str, skip=()) -> None:
    """Rewrite every value of `column` whose mount point is not normalized."""
    skip = frozenset(skip)
    rows = connection.query_all(f"SELECT DISTINCT {column} FROM {table}")
    changes = [
        (new, old)
        for old in (row[column] for row in rows)
        if old and old not in skip and (new := normalize_mount_point(old)) != old
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
        conflicts = find_filename_conflicts(connection)
        if conflicts:
            _report_conflicts(conflicts)
        # Every spelling of a conflict is skipped, not just the losers: folding
        # any of them would collide with the others on UNIQUE(filename).
        conflicting = {name for names in conflicts for name in names}
        _normalize_column(connection, "video", "filename", skip=conflicting)
        _normalize_column(connection, "video", "driver_id")
        _deduplicate_sources(connection)
        _normalize_column(connection, "collection_source", "source")
