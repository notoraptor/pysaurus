"""Migration to version 2: baseline schema additions.

Applies all ALTER TABLE statements that were previously run on every
database open (similarity_id_reencoded, byte_rate rename,
filename-derived virtual columns).  These are idempotent — they silently
fail if the column already exists or has already been dropped.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skullite import Skullite

_STATEMENTS = [
    "ALTER TABLE video ADD COLUMN similarity_id_reencoded INTEGER",
    # Rename virtual column bit_rate -> byte_rate
    "ALTER TABLE video DROP COLUMN bit_rate",
    (
        "ALTER TABLE video ADD COLUMN byte_rate DOUBLE GENERATED ALWAYS AS"
        " (IIF(duration = 0, 0, file_size *"
        " COALESCE(NULLIF(duration_time_base, 0), 1) / duration)) VIRTUAL"
    ),
    # Filename-derived virtual columns for searchexp
    (
        "ALTER TABLE video ADD COLUMN _basename TEXT GENERATED ALWAYS AS"
        " (IIF("
        " RTRIM(REPLACE(filename, char(92), '/'), REPLACE(REPLACE(filename, char(92), '/'), '/', '')) = '',"
        " REPLACE(filename, char(92), '/'),"
        " SUBSTR(REPLACE(filename, char(92), '/'), LENGTH(RTRIM(REPLACE(filename, char(92), '/'), REPLACE(REPLACE(filename, char(92), '/'), '/', ''))) + 1)"
        " )) VIRTUAL"
    ),
    (
        "ALTER TABLE video ADD COLUMN extension TEXT GENERATED ALWAYS AS"
        " (CASE"
        " WHEN RTRIM(_basename, REPLACE(_basename, '.', '')) = '' OR LENGTH(RTRIM(_basename, REPLACE(_basename, '.', ''))) = 1 THEN ''"
        " ELSE LOWER(SUBSTR(_basename, LENGTH(RTRIM(_basename, REPLACE(_basename, '.', ''))) + 1))"
        " END) VIRTUAL"
    ),
    (
        "ALTER TABLE video ADD COLUMN file_title TEXT GENERATED ALWAYS AS"
        " (CASE"
        " WHEN RTRIM(_basename, REPLACE(_basename, '.', '')) = '' THEN _basename"
        " WHEN LENGTH(RTRIM(_basename, REPLACE(_basename, '.', ''))) = 1 THEN SUBSTR(_basename, 2)"
        " ELSE SUBSTR(_basename, 1, LENGTH(RTRIM(_basename, REPLACE(_basename, '.', ''))) - 1)"
        " END) VIRTUAL"
    ),
]


def migrate(db: Skullite) -> None:
    for sql in _STATEMENTS:
        try:
            with db.connect() as connection:
                connection.modify(sql)
        except Exception:
            pass  # Column already exists or table doesn't have old column
