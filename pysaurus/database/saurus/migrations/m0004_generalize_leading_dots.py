"""Migration to version 4: generalize leading-dot handling in extension/file_title.

The previous formula only special-cased a *single* leading dot (e.g.
".gitignore" -> no extension). A run of two or more leading dots followed by
a dot-free remainder (e.g. "..backup") fell through to the normal split
instead, disagreeing with AbsolutePath.extension/.file_title (which follow
os.path.splitext's convention of treating any run of leading dots as part of
the root, not a separator).

SQLite does not support ``ALTER TABLE ... ALTER COLUMN`` to change a
generated column's expression, so we must rebuild the whole ``video`` table,
same as m0003.
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

# Distinctive substring of the generalized formula (absent from both the
# original VIRTUAL-era and m0003 STORED-era formulas), used to detect
# whether this migration already ran.
_GENERALIZED_FORMULA_MARKER = "REPLACE(RTRIM(_basename"


def _needs_rebuild(db: Skullite) -> bool:
    """Return True unless the video table already uses the generalized formula."""
    with db.connect() as connection:
        rows = connection.query_all(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='video'"
        )
    if not rows:
        return False  # No video table yet: schema.sql will create it correctly.
    return _GENERALIZED_FORMULA_MARKER not in rows[0]["sql"]


def _rebuild_video_table(db: Skullite) -> None:
    """Rebuild the video table with the generalized extension/file_title formula.

    Same rebuild pattern as m0003: create _video_new, copy real columns,
    drop the old table, rename. Foreign keys are turned off so DROP doesn't
    cascade-delete related tables and RENAME doesn't rewrite FK references.
    Triggers (FTS5 etc.) are lost on DROP; the caller must re-run
    database.sql to recreate them.
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


# Full CREATE TABLE statement for the video table with the generalized
# extension/file_title formula. Must stay in sync with database.sql.
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
            WHEN REPLACE(RTRIM(_basename, REPLACE(_basename, '.', '')), '.', '') = '' THEN ''
            ELSE LOWER(SUBSTR(_basename, LENGTH(RTRIM(_basename, REPLACE(_basename, '.', ''))) + 1))
        END
    ) STORED,
    file_title TEXT GENERATED ALWAYS AS (
        CASE
            WHEN REPLACE(RTRIM(_basename, REPLACE(_basename, '.', '')), '.', '') = '' THEN SUBSTR(_basename, LENGTH(RTRIM(_basename, REPLACE(_basename, '.', ''))) + 1)
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
