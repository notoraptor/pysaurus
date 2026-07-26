"""Migration m0005 brings pre-existing bool properties in line.

PropType now refuses a multiple or enumerated bool, including when rebuilt
from the database, so a database written before that rule has to be fixed on
open or it would become unreadable.
"""

import sqlite3
from pathlib import Path

import pytest

from pysaurus.database.saurus.prop_type_search import prop_type_search
from pysaurus.database.saurus.pysaurus_connection import PysaurusConnection

# The property table as it stood before m0005: same as database.sql minus the
# bool CHECK. Recreating it is what makes the fixture a genuine pre-migration
# database, and what makes the rebuild path actually run.
_LEGACY_PROPERTY_TABLE = """
CREATE TABLE property (
	property_id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	type TEXT NOT NULL,
	multiple INTEGER NOT NULL DEFAULT 0,
	CHECK (type IN ("bool", "int", "float", "str")),
	CHECK (multiple IN (0, 1)),
	UNIQUE (name)
);
"""


_FILENAMES = ["/videos/both.mp4", "/videos/false_only.mp4", "/videos/untagged.mp4"]


@pytest.fixture
def legacy_db_path(tmp_path) -> Path:
    """A database in a pre-m0005 state, built from scratch.

    It holds every shape m0005 has to deal with:

    - ``flag``: the broken case -- a *multiple* bool with a spurious enumeration
      row, one video holding both values at once and one holding only False;
    - ``watched``: the ordinary case -- a *unique* bool with mixed values across
      videos, which the migration must leave strictly alone;
    - ``orphan``: a bool with no enumeration row at all, for the seeding path;
    - ``category``: a str property, to check nothing else is touched.

    Built rather than copied from the on-disk fixture: this needs the schema,
    not 10k videos, and copying 31 MB per test adds up.
    """
    path = tmp_path / "legacy.db"

    # A fresh database first, so triggers and custom SQL functions are in place
    # for the video inserts below.
    db = PysaurusConnection(str(path))
    video_ids = [
        db.modify("INSERT INTO video (filename) VALUES (?)", [filename])
        for filename in _FILENAMES
    ]
    del db
    both, false_only, _untagged = video_ids

    raw = sqlite3.connect(path)
    try:
        # Roll the property table back to its pre-m0005 shape. The view selects
        # from it, so it goes first and the migration is expected to restore it.
        raw.executescript(
            "PRAGMA foreign_keys = OFF;"
            "DROP VIEW IF EXISTS video_property_text;"
            "DROP TABLE property;" + _LEGACY_PROPERTY_TABLE
        )
        flag_id = raw.execute(
            "INSERT INTO property (name, type, multiple) VALUES ('flag', 'bool', 1)"
        ).lastrowid
        watched_id = raw.execute(
            "INSERT INTO property (name, type, multiple) VALUES ('watched', 'bool', 0)"
        ).lastrowid
        raw.execute(
            "INSERT INTO property (name, type, multiple) VALUES ('orphan', 'bool', 0)"
        )
        raw.execute(
            "INSERT INTO property (name, type, multiple) VALUES ('category', 'str', 1)"
        )
        raw.executemany(
            "INSERT INTO property_enumeration (property_id, enum_value, rank) "
            "VALUES (?, ?, ?)",
            [(flag_id, "0", 0), (flag_id, "1", 1), (watched_id, "0", 0)],
        )
        raw.executemany(
            "INSERT INTO video_property_value (video_id, property_id, property_value) "
            "VALUES (?, ?, ?)",
            [
                (both, flag_id, "0"),
                (both, flag_id, "1"),
                (false_only, flag_id, "0"),
                # A unique bool: at most one value per video, both values used.
                (both, watched_id, "1"),
                (false_only, watched_id, "0"),
            ],
        )
        raw.execute("UPDATE collection SET version = 4 WHERE collection_id = 0")
        raw.commit()
    finally:
        raw.close()
    return path


def _property(db: PysaurusConnection, name: str = "flag") -> dict:
    (row,) = db.query_all("SELECT * FROM property WHERE name = ?", [name])
    return dict(row)


def _values_by_video(db: PysaurusConnection, name: str) -> dict[str, list[str]]:
    """Stored values of a property, keyed by video filename."""
    rows = db.query_all(
        "SELECT v.filename AS filename, pv.property_value AS value "
        "FROM video_property_value AS pv "
        "JOIN video AS v ON v.video_id = pv.video_id "
        "JOIN property AS p ON p.property_id = pv.property_id "
        "WHERE p.name = ? ORDER BY v.filename, pv.property_value",
        [name],
    )
    values: dict[str, list[str]] = {}
    for row in rows:
        values.setdefault(row["filename"], []).append(row["value"])
    return values


def test_migration_makes_bool_unique(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    assert _property(db)["multiple"] == 0


def test_migration_keeps_only_the_default_enum_row(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    prop_id = _property(db)["property_id"]
    rows = db.query_all(
        "SELECT enum_value, rank FROM property_enumeration WHERE property_id = ?",
        [prop_id],
    )
    assert [dict(row) for row in rows] == [{"enum_value": "0", "rank": 0}]


def test_migration_collapses_videos_holding_both_values(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    # One value per video, True winning over False (deterministic, not arbitrary)
    # -- and *only* for the video that held both: a video holding only False
    # keeps it, since the keeper is picked per video and not per property.
    assert _values_by_video(db, "flag") == {
        "/videos/both.mp4": ["1"],
        "/videos/false_only.mp4": ["0"],
    }


def test_migration_leaves_a_unique_bool_untouched(legacy_db_path):
    """A bool that was already unique has nothing to collapse.

    Regression guard: correlating the keeper on the wrong scope makes MAX a
    per-property maximum, which silently deletes every False of the property
    as soon as one video holds True.
    """
    db = PysaurusConnection(str(legacy_db_path))
    assert _values_by_video(db, "watched") == {
        "/videos/both.mp4": ["1"],
        "/videos/false_only.mp4": ["0"],
    }


def test_migration_seeds_a_default_when_none_exists(legacy_db_path):
    """prop_type_search reads the default as enumeration[0]; it must exist."""
    db = PysaurusConnection(str(legacy_db_path))
    prop_id = _property(db, "orphan")["property_id"]
    rows = db.query_all(
        "SELECT enum_value, rank FROM property_enumeration WHERE property_id = ?",
        [prop_id],
    )
    assert [dict(row) for row in rows] == [{"enum_value": "0", "rank": 0}]
    (prop,) = [pt for pt in prop_type_search(db) if pt.name == "orphan"]
    assert prop.default == [False]


def test_migrated_property_reads_back(legacy_db_path):
    """The whole point: prop_type_search must not raise on it any more."""
    db = PysaurusConnection(str(legacy_db_path))
    (prop,) = [pt for pt in prop_type_search(db) if pt.name == "flag"]
    assert prop.type == "bool"
    assert prop.multiple is False
    assert prop.enumeration is None
    assert prop.possible_values == [False, True]
    assert prop.default == [False]


def test_migration_adds_the_check_constraint(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    with pytest.raises(Exception, match="CHECK constraint failed"):
        db.modify("UPDATE property SET multiple = 1 WHERE name = 'flag'")


def test_migration_leaves_other_properties_alone(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    rows = db.query_all(
        "SELECT name, type, multiple FROM property WHERE type != 'bool'"
    )
    assert [dict(row) for row in rows] == [
        {"name": "category", "type": "str", "multiple": 1}
    ]


def test_migration_restores_the_dropped_view(legacy_db_path):
    """The property table rebuild drops video_property_text; schema.sql re-adds it."""
    db = PysaurusConnection(str(legacy_db_path))
    assert db.query_all(
        "SELECT name FROM sqlite_master WHERE type = 'view' "
        "AND name = 'video_property_text'"
    )


def test_migration_is_idempotent(legacy_db_path):
    PysaurusConnection(str(legacy_db_path))
    db = PysaurusConnection(str(legacy_db_path))  # second open: nothing left to do
    assert dict(db.query_all("SELECT version FROM collection")[0])["version"] == 5
    assert _property(db)["multiple"] == 0


def test_fresh_database_carries_the_check(tmp_path):
    """A database created from scratch gets the constraint from database.sql."""
    db = PysaurusConnection(str(tmp_path / "fresh.db"))
    db.modify("INSERT INTO property (name, type, multiple) VALUES ('f','bool',0)")
    with pytest.raises(Exception, match="CHECK constraint failed"):
        db.modify("INSERT INTO property (name, type, multiple) VALUES ('g','bool',1)")
