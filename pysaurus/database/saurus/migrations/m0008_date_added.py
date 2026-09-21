"""Migration to version 8: give every video a date of its own.

``date_added`` is when the content entered the collection: the file's mtime at
insertion, kept across rescans, and carried over when an entry is merged into
another one (a move, a re-encoded copy). Existing rows start from their mtime.
It is a field of its own: ``mtime`` stays the file date behind ``date``, ``day``
and ``year``.

A plain column, so ``ALTER TABLE ADD COLUMN`` and no table rebuild. The backfill
only fills rows still at the default, so a replay never overwrites a date.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skullite import Skullite


def migrate(db: Skullite) -> None:
    with db.connect() as connection:
        existing = {
            row["name"] for row in connection.query_all("PRAGMA table_xinfo(video)")
        }
        if "date_added" not in existing:
            connection.modify(
                "ALTER TABLE video ADD COLUMN date_added DOUBLE NOT NULL DEFAULT 0.0"
            )
        connection.modify("UPDATE video SET date_added = mtime WHERE date_added = 0")
