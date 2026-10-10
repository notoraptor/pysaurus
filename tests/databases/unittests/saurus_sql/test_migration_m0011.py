"""Migration m0011 adds the saved_search table, empty."""

from pathlib import Path

import pytest

from pysaurus.database.saurus.migrations import LATEST_VERSION, m0011_saved_search
from pysaurus.database.saurus.pysaurus_connection import PysaurusConnection


def _legacy_db(path: Path) -> Path:
    """A version-10 database: no saved_search table."""
    db = PysaurusConnection(str(path))
    db.modify("DROP TABLE saved_search")
    db.modify("UPDATE collection SET version = 10")
    return path


@pytest.fixture
def legacy_db_path(tmp_path) -> Path:
    return _legacy_db(tmp_path / "legacy.db")


def _count(db: PysaurusConnection) -> int:
    return db.query_all("SELECT COUNT(*) AS n FROM saved_search")[0]["n"]


def test_table_is_created_empty(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    assert db.get_version() == LATEST_VERSION
    assert _count(db) == 0


def test_replay_keeps_rows(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    db.modify("INSERT INTO saved_search (expression, name) VALUES ('width > 1', 'w')")
    m0011_saved_search.migrate(db)
    assert _count(db) == 1
