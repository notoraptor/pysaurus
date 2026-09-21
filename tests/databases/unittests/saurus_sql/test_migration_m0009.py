"""Migration m0009 adds the settings column to the collection row, as a foreign
key that clears itself when the property goes."""

from pathlib import Path

import pytest

from pysaurus.database.saurus.migrations import LATEST_VERSION, m0009_database_settings
from pysaurus.database.saurus.pysaurus_connection import PysaurusConnection

_COLLECTION_V8 = (
    "CREATE TABLE collection_v8 ("
    " collection_id INTEGER PRIMARY KEY AUTOINCREMENT,"
    " name TEXT NOT NULL,"
    " version INTEGER NOT NULL DEFAULT -1,"
    " date_updated DOUBLE,"
    " CHECK (collection_id = 0))"
)


def _legacy_db(path: Path) -> Path:
    """A version-8 database: the collection table without the settings column.

    The column cannot be dropped (SQLite refuses to drop a foreign key), so the
    table is rebuilt from its version-8 definition.
    """
    db = PysaurusConnection(str(path))
    db.modify("INSERT INTO property (name, type, multiple) VALUES ('p', 'str', 0)")
    for statement in (
        _COLLECTION_V8,
        "INSERT INTO collection_v8"
        " SELECT collection_id, name, 8, date_updated FROM collection",
        "DROP TABLE collection",
        "ALTER TABLE collection_v8 RENAME TO collection",
    ):
        db.modify(statement)
    return path


@pytest.fixture
def legacy_db_path(tmp_path) -> Path:
    return _legacy_db(tmp_path / "legacy.db")


def _columns(db: PysaurusConnection) -> list[str]:
    return [row["name"] for row in db.query_all("PRAGMA table_info(collection)")]


def _setting(db: PysaurusConnection):
    return db.query_all("SELECT generalize_title_property_id AS v FROM collection")[0][
        "v"
    ]


def test_column_is_added_and_empty(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    assert db.get_version() == LATEST_VERSION
    assert "generalize_title_property_id" in _columns(db)
    assert _setting(db) is None


def test_added_column_is_a_live_foreign_key(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    (prop,) = db.query_all("SELECT property_id FROM property WHERE name = 'p'")
    db.modify(
        "UPDATE collection SET generalize_title_property_id = ?", [prop["property_id"]]
    )
    assert _setting(db) == prop["property_id"]
    db.modify("DELETE FROM property WHERE name = 'p'")
    assert _setting(db) is None


def test_replay_is_a_no_op(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    m0009_database_settings.migrate(db)
    assert _columns(db).count("generalize_title_property_id") == 1
