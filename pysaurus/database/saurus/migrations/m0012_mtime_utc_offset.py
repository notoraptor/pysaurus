"""Migration to version 12: remember the local UTC offset behind each mtime.

FAT32, and exFAT entries written without a UTC offset, store local wall time
that the OS converts with the offset in effect when it reads. The reported
mtime of an untouched file therefore moves by the change of offset between two
scans, which used to re-process whole drives at every DST switch. Recording
the offset of each reading lets the update accept exactly that drift and
nothing else. Existing rows get NULL: the update grants them an hour of slack
once, then stamps them.
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
        if "mtime_utc_offset" not in existing:
            connection.modify("ALTER TABLE video ADD COLUMN mtime_utc_offset INTEGER")
