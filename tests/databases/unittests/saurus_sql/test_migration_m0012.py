"""Migration m0012 adds video.mtime_utc_offset, NULL on existing rows."""

from pathlib import Path

import pytest

from pysaurus.database.saurus.migrations import LATEST_VERSION, m0012_mtime_utc_offset
from pysaurus.database.saurus.pysaurus_connection import PysaurusConnection


def _columns(db: PysaurusConnection) -> set[str]:
    return {row["name"] for row in db.query_all("PRAGMA table_xinfo(video)")}


def _offsets(db: PysaurusConnection) -> list:
    return [
        row["mtime_utc_offset"]
        for row in db.query_all("SELECT mtime_utc_offset FROM video")
    ]


@pytest.fixture
def legacy_db_path(tmp_path) -> Path:
    """A version-11 database with one video and no mtime_utc_offset column."""
    path = tmp_path / "legacy.db"
    db = PysaurusConnection(str(path))
    db.modify("ALTER TABLE video DROP COLUMN mtime_utc_offset")
    db.modify("UPDATE collection SET version = 11")
    assert "mtime_utc_offset" not in _columns(db)
    db.modify("INSERT INTO video (filename) VALUES ('C:\\a.mkv')")
    return path


def test_column_is_added_null_on_existing_rows(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    assert db.get_version() == LATEST_VERSION
    assert "mtime_utc_offset" in _columns(db)
    assert _offsets(db) == [None]


def test_replay_keeps_values(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    db.modify("UPDATE video SET mtime_utc_offset = -18000")
    m0012_mtime_utc_offset.migrate(db)
    assert _offsets(db) == [-18000]
