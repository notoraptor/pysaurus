"""Migration m0008 gives every video a ``date_added`` seeded from its mtime and
leaves ``day``/``year`` on the file date."""

from pathlib import Path

import pytest

from pysaurus.database.saurus.migrations import LATEST_VERSION, m0008_date_added
from pysaurus.database.saurus.pysaurus_connection import PysaurusConnection

TS_2019 = 1_546_300_800.0  # 2019-01-01 UTC
TS_2026 = 1_767_225_600.0  # 2026-01-01 UTC
OLD, NEW = "C:\\old.mkv", "C:\\new.mkv"


def _legacy_db(path: Path) -> Path:
    """A version-7 database, without date_added.

    Built and downgraded through PysaurusConnection: the FTS5 triggers reference
    Python-side SQL functions, so a plain sqlite3 connection cannot even alter
    the table.
    """
    db = PysaurusConnection(str(path))
    for filename, mtime in ((OLD, TS_2019), (NEW, TS_2026)):
        db.modify(
            "INSERT INTO video (filename, mtime) VALUES (?, ?)", [filename, mtime]
        )
    for statement in (
        "DROP INDEX IF EXISTS idx_video_date_added",
        "ALTER TABLE video DROP COLUMN date_added",
        "UPDATE collection SET version = 7 WHERE collection_id = 0",
    ):
        db.modify(statement)
    return path


@pytest.fixture
def legacy_db_path(tmp_path) -> Path:
    return _legacy_db(tmp_path / "legacy.db")


def _rows(db: PysaurusConnection) -> dict[str, dict]:
    return {
        row["filename"]: dict(row)
        for row in db.query_all(
            "SELECT filename, mtime, date_added, day, year FROM video"
        )
    }


def test_date_added_is_seeded_from_mtime(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    assert db.get_version() == LATEST_VERSION
    rows = _rows(db)
    assert rows[OLD]["date_added"] == TS_2019
    assert rows[NEW]["date_added"] == TS_2026


def test_day_and_year_stay_on_the_file_date(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    db.modify("UPDATE video SET date_added = ? WHERE filename = ?", [TS_2019, NEW])
    row = _rows(db)[NEW]
    assert row["mtime"] == TS_2026
    assert (row["day"], row["year"]) == ("2026-01-01", "2026")


def test_replay_never_overwrites_a_date(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    db.modify("UPDATE video SET date_added = ? WHERE filename = ?", [TS_2019, NEW])
    m0008_date_added.migrate(db)
    assert _rows(db)[NEW]["date_added"] == TS_2019
