"""Migration m0010 adds the copy-overwrite flag to the collection row, off."""

from pathlib import Path

import pytest

from pysaurus.database.saurus.migrations import (
    LATEST_VERSION,
    m0010_copy_overwrites_unique,
)
from pysaurus.database.saurus.pysaurus_connection import PysaurusConnection

COLUMN = "copy_overwrites_unique_properties"


def _legacy_db(path: Path) -> Path:
    """A version-9 database: the collection row without the flag column."""
    db = PysaurusConnection(str(path))
    db.modify(f"ALTER TABLE collection DROP COLUMN {COLUMN}")
    db.modify("UPDATE collection SET version = 9")
    return path


@pytest.fixture
def legacy_db_path(tmp_path) -> Path:
    return _legacy_db(tmp_path / "legacy.db")


def _columns(db: PysaurusConnection) -> list[str]:
    return [row["name"] for row in db.query_all("PRAGMA table_info(collection)")]


def test_column_is_added_and_off(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    assert db.get_version() == LATEST_VERSION
    assert COLUMN in _columns(db)
    assert db.query_all(f"SELECT {COLUMN} AS v FROM collection")[0]["v"] == 0


def test_replay_is_a_no_op(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    m0010_copy_overwrites_unique.migrate(db)
    assert _columns(db).count(COLUMN) == 1
