"""Migration to version 3: convert _basename/extension/file_title to STORED.

VIRTUAL generated columns are recomputed on every read and cannot be
indexed.  STORED columns are computed once at write time, persisted on
disk, and indexable.

SQLite does not support ``ALTER TABLE ADD COLUMN ... STORED``, so we
must rebuild the whole ``video`` table.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skullite import Skullite

# Non-generated columns of the video table (order matches database.sql).
_REAL_COLUMNS = (
    "video_id",
    "filename",
    "file_size",
    "unreadable",
    "audio_bit_rate",
    "audio_bits",
    "audio_codec",
    "audio_codec_description",
    "bit_depth",
    "channels",
    "container_format",
    "device_name",
    "duration",
    "duration_time_base",
    "frame_rate_den",
    "frame_rate_num",
    "height",
    "meta_title",
    "sample_rate",
    "video_codec",
    "video_codec_description",
    "width",
    "mtime",
    "driver_id",
    "is_file",
    "discarded",
    "date_entry_modified",
    "date_entry_opened",
    "similarity_id",
    "similarity_id_reencoded",
    "watched",
)


def _needs_rebuild(db: Skullite) -> bool:
    """Return True unless _basename is already a STORED column (hidden == 3).

    Covers three states: missing (None), VIRTUAL (2), and STORED (3).
    Only STORED means the rebuild already happened.
    """
    with db.connect() as connection:
        rows = connection.query_all("PRAGMA table_xinfo(video)")
    col_hidden = {row["name"]: row["hidden"] for row in rows}
    return col_hidden.get("_basename") != 3


def _rebuild_video_table(db: Skullite) -> None:
    """Rebuild the video table with STORED filename-derived columns.

    Uses the standard SQLite table-rebuild pattern:
    1. Create _video_new with STORED columns
    2. Copy all non-generated columns
    3. DROP old video table
    4. RENAME _video_new → video

    Foreign keys must be OFF so that:
    - DROP TABLE doesn't cascade-delete from related tables
    - RENAME doesn't rewrite FK references in other tables
      (they already say ``video``, and will resolve after the rename)

    Triggers (FTS5 etc.) attached to the old video table are lost
    on DROP; the caller must re-run database.sql to recreate them.
    """
    cols = ", ".join(_REAL_COLUMNS)
    with db.connect() as connection:
        connection.modify("PRAGMA foreign_keys = OFF")
        connection.script(_CREATE_VIDEO_TABLE_NEW)
        connection.modify(f"INSERT INTO _video_new ({cols}) SELECT {cols} FROM video")
        connection.modify("DROP TABLE video")
        connection.modify("ALTER TABLE _video_new RENAME TO video")
        connection.modify("PRAGMA foreign_keys = ON")


def _create_indexes(db: Skullite) -> None:
    with db.connect() as connection:
        connection.modify(
            "CREATE INDEX IF NOT EXISTS idx_video_extension ON video(extension)"
        )
        connection.modify(
            "CREATE INDEX IF NOT EXISTS idx_video_file_title ON video(file_title)"
        )


def migrate(db: Skullite) -> None:
    if _needs_rebuild(db):
        _rebuild_video_table(db)
    _create_indexes(db)


# Full CREATE TABLE statement for the video table with STORED filename columns.
# Must stay in sync with database.sql.
_CREATE_VIDEO_TABLE_NEW = """\
CREATE TABLE _video_new (
    video_id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    unreadable INTEGER NOT NULL DEFAULT 0,
    audio_bit_rate INTEGER NOT NULL DEFAULT 0,
    audio_bits INTEGER NOT NULL DEFAULT 0,
    audio_codec TEXT NOT NULL DEFAULT "",
    audio_codec_description TEXT NOT NULL DEFAULT "",
    bit_depth INTEGER NOT NULL DEFAULT 0,
    channels INTEGER NOT NULL DEFAULT 0,
    container_format TEXT NOT NULL DEFAULT "",
    device_name TEXT NOT NULL DEFAULT "",
    duration DOUBLE NOT NULL DEFAULT 0.0,
    duration_time_base INTEGER NOT NULL DEFAULT 0,
    frame_rate_den INTEGER NOT NULL DEFAULT 0,
    frame_rate_num INTEGER NOT NULL DEFAULT 0,
    height INTEGER NOT NULL DEFAULT 0,
    meta_title TEXT NOT NULL DEFAULT "",
    sample_rate INTEGER NOT NULL DEFAULT 0,
    video_codec TEXT NOT NULL DEFAULT "",
    video_codec_description TEXT NOT NULL DEFAULT "",
    width INTEGER NOT NULL DEFAULT 0,
    mtime DOUBLE NOT NULL DEFAULT 0.0,
    driver_id TEXT,
    is_file INTEGER NOT NULL DEFAULT 0,
    discarded INTEGER NOT NULL DEFAULT 0,
    date_entry_modified DOUBLE,
    date_entry_opened DOUBLE,
    similarity_id INTEGER,
    similarity_id_reencoded INTEGER,
    watched INTEGER NOT NULL DEFAULT 0,
    -- virtual columns
    readable INTEGER GENERATED ALWAYS AS (1 - unreadable) VIRTUAL,
    found INTEGER GENERATED ALWAYS AS (is_file) VIRTUAL,
    not_found INTEGER GENERATED ALWAYS AS (1 - is_file) VIRTUAL,
    duration_time_base_not_null INTEGER GENERATED ALWAYS AS (COALESCE(NULLIF(duration_time_base, 0), 1)) VIRTUAL,
    length_seconds DOUBLE GENERATED ALWAYS AS ((duration * 1.0 / duration_time_base_not_null)) VIRTUAL,
    length_microseconds DOUBLE GENERATED ALWAYS AS ((duration * 1000000.0 / duration_time_base_not_null)) VIRTUAL,
    byte_rate DOUBLE GENERATED ALWAYS AS (IIF(duration = 0, 0, file_size * duration_time_base_not_null / duration)) VIRTUAL,
    date_entry_modified_not_null DOUBLE GENERATED ALWAYS AS (COALESCE(date_entry_modified, mtime)) VIRTUAL,
    date_entry_opened_not_null DOUBLE GENERATED ALWAYS AS (COALESCE(date_entry_opened, mtime)) VIRTUAL,
    day TEXT GENERATED ALWAYS AS (strftime('%Y-%m-%d', datetime(mtime, 'unixepoch'))) VIRTUAL,
    year TEXT GENERATED ALWAYS AS (strftime('%Y', datetime(mtime, 'unixepoch'))) VIRTUAL,
    frame_rate DOUBLE GENERATED ALWAYS AS (frame_rate_num * 1.0 / COALESCE(NULLIF(frame_rate_den, 0), 1)) VIRTUAL,
    -- filename-derived stored columns
    _basename TEXT GENERATED ALWAYS AS (
        IIF(
            RTRIM(REPLACE(filename, char(92), '/'), REPLACE(REPLACE(filename, char(92), '/'), '/', '')) = '',
            REPLACE(filename, char(92), '/'),
            SUBSTR(
                REPLACE(filename, char(92), '/'),
                LENGTH(RTRIM(REPLACE(filename, char(92), '/'), REPLACE(REPLACE(filename, char(92), '/'), '/', ''))) + 1
            )
        )
    ) STORED,
    extension TEXT GENERATED ALWAYS AS (
        CASE
            WHEN RTRIM(_basename, REPLACE(_basename, '.', '')) = '' OR LENGTH(RTRIM(_basename, REPLACE(_basename, '.', ''))) = 1 THEN ''
            ELSE LOWER(SUBSTR(_basename, LENGTH(RTRIM(_basename, REPLACE(_basename, '.', ''))) + 1))
        END
    ) STORED,
    file_title TEXT GENERATED ALWAYS AS (
        CASE
            WHEN RTRIM(_basename, REPLACE(_basename, '.', '')) = '' THEN _basename
            WHEN LENGTH(RTRIM(_basename, REPLACE(_basename, '.', ''))) = 1 THEN SUBSTR(_basename, 2)
            ELSE SUBSTR(_basename, 1, LENGTH(RTRIM(_basename, REPLACE(_basename, '.', ''))) - 1)
        END
    ) STORED,
    -- constraints
    CHECK (is_file IN (0, 1)),
    CHECK (discarded IN (0, 1)),
    CHECK (unreadable IN (0, 1)),
    UNIQUE (filename)
);
"""
