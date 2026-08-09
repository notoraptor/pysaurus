"""Migration m0006 normalizes the mount point of every stored path.

A database written before the rule can hold one file under two spellings of
its drive, which never compare equal: the folder scan reports indexed videos
as unknown, and the "disk" grouping splits in two.
"""

import logging
import os
import sqlite3
from pathlib import Path

import pytest

from pysaurus.database.saurus.migrations.m0006_normalize_mount_points import (
    find_filename_conflicts,
)
from pysaurus.database.saurus.pysaurus_connection import PysaurusConnection

windows_only = pytest.mark.skipif(
    os.name != "nt", reason="splitdrive finds no prefix on POSIX"
)


def _legacy_db(path: Path, videos: list[tuple], sources: list[str] = ()) -> Path:
    """A database at version 5 holding the given raw (filename, driver_id) rows.

    Rows go in through PysaurusConnection: the FTS5 triggers call Python-side
    SQL functions that a plain sqlite3 connection does not carry. Only the
    version rollback, which fires nothing, is done raw.
    """
    db = PysaurusConnection(str(path))
    for filename, driver_id in videos:
        db.modify(
            "INSERT INTO video (filename, driver_id) VALUES (?, ?)",
            [filename, driver_id],
        )
    for source in sources:
        db.modify("INSERT INTO collection_source (source) VALUES (?)", [source])
    del db

    raw = sqlite3.connect(path)
    try:
        raw.execute("UPDATE collection SET version = 5 WHERE collection_id = 0")
        raw.commit()
    finally:
        raw.close()
    return path


@pytest.fixture
def legacy_db_path(tmp_path) -> Path:
    """Both drive spellings, a mixed-case basename, and a POSIX-style path."""
    return _legacy_db(
        tmp_path / "legacy.db",
        [
            ("C:\\Videos\\A Film.mkv", "C:\\"),
            ("c:\\Videos\\Another Film.mkv", "c:\\"),
            ("/videos/on_posix.mkv", "/"),
        ],
        ["C:\\Videos", "c:\\Videos", "D:\\Other"],
    )


def _filenames(db: PysaurusConnection) -> list[str]:
    return sorted(row["filename"] for row in db.query_all("SELECT filename FROM video"))


@windows_only
def test_filenames_get_a_normalized_drive(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    assert _filenames(db) == [
        "/videos/on_posix.mkv",
        "C:\\Videos\\A Film.mkv",
        "C:\\Videos\\Another Film.mkv",
    ]


@windows_only
def test_only_the_drive_is_touched(legacy_db_path):
    """The whole point of normalizing the mount point alone: titles survive."""
    db = PysaurusConnection(str(legacy_db_path))
    titles = sorted(row["file_title"] for row in db.query_all("SELECT * FROM video"))
    assert titles == ["A Film", "Another Film", "on_posix"]


@windows_only
def test_driver_ids_are_normalized(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    drivers = {row["driver_id"] for row in db.query_all("SELECT driver_id FROM video")}
    assert drivers == {"C:\\", "/"}


@windows_only
def test_sources_are_normalized_and_deduplicated(legacy_db_path):
    db = PysaurusConnection(str(legacy_db_path))
    sources = sorted(
        row["source"] for row in db.query_all("SELECT source FROM collection_source")
    )
    assert sources == ["C:\\Videos", "D:\\Other"]


def test_paths_without_a_drive_are_left_alone(tmp_path):
    """POSIX paths have no prefix to normalize, on any platform."""
    path = _legacy_db(tmp_path / "posix.db", [("/videos/Mixed Case.mkv", "/mnt/Data")])
    db = PysaurusConnection(str(path))
    assert _filenames(db) == ["/videos/Mixed Case.mkv"]
    assert db.query_all("SELECT driver_id FROM video")[0]["driver_id"] == "/mnt/Data"


@pytest.fixture
def conflict_db_path(tmp_path) -> Path:
    """One file under both spellings, plus an unrelated row to be migrated."""
    return _legacy_db(
        tmp_path / "conflict.db",
        [
            ("C:\\Videos\\a.mkv", "C:\\"),
            ("c:\\Videos\\a.mkv", "c:\\"),
            ("c:\\Videos\\clean.mkv", "c:\\"),
        ],
    )


@windows_only
def test_a_conflict_does_not_block_opening(conflict_db_path):
    """Refusing would lock the user out: merging needs the application."""
    db = PysaurusConnection(str(conflict_db_path))
    assert db.query_all("SELECT version FROM collection")[0]["version"] == 6


@windows_only
def test_conflicting_rows_are_left_untouched(conflict_db_path):
    db = PysaurusConnection(str(conflict_db_path))
    stored = _filenames(db)
    # Both spellings survive, exactly as they are today. Folding either one
    # would collide with the other on UNIQUE(filename).
    assert "C:\\Videos\\a.mkv" in stored
    assert "c:\\Videos\\a.mkv" in stored


@windows_only
def test_rows_without_a_conflict_are_still_migrated(conflict_db_path):
    """A conflict must not stop the rest of the database from being fixed."""
    db = PysaurusConnection(str(conflict_db_path))
    assert "C:\\Videos\\clean.mkv" in _filenames(db)
    drivers = {row["driver_id"] for row in db.query_all("SELECT driver_id FROM video")}
    assert drivers == {"C:\\"}


@windows_only
def test_conflicts_are_reported(conflict_db_path, caplog):
    """The only channel available at open time -- there is no UI yet."""
    with caplog.at_level(logging.WARNING):
        PysaurusConnection(str(conflict_db_path))
    (record,) = [r for r in caplog.records if "several spellings" in r.getMessage()]
    message = record.getMessage()
    assert "C:\\Videos\\a.mkv" in message and "c:\\Videos\\a.mkv" in message
    assert "clean.mkv" not in message


@windows_only
def test_the_conflict_is_announced_once_and_survives(conflict_db_path, caplog):
    """The migration runs once, so it neither repeats nor resolves anything.

    The warning wording must match that: it used to promise the rows would be
    normalized "on a later run", which never comes.
    """
    with caplog.at_level(logging.WARNING):
        PysaurusConnection(str(conflict_db_path))
        first = [r for r in caplog.records if "several spellings" in r.getMessage()]
        caplog.clear()
        PysaurusConnection(str(conflict_db_path))
        second = [r for r in caplog.records if "several spellings" in r.getMessage()]
    assert len(first) == 1 and not second
    with PysaurusConnection(str(conflict_db_path)).connect() as connection:
        assert find_filename_conflicts(connection) == [
            ["C:\\Videos\\a.mkv", "c:\\Videos\\a.mkv"]
        ]


def test_migration_is_idempotent(legacy_db_path):
    PysaurusConnection(str(legacy_db_path))
    db = PysaurusConnection(str(legacy_db_path))  # second open: nothing left to do
    assert db.query_all("SELECT version FROM collection")[0]["version"] == 6
    assert len(_filenames(db)) == 3


def test_fresh_database_is_at_the_latest_version(tmp_path):
    db = PysaurusConnection(str(tmp_path / "fresh.db"))
    assert db.query_all("SELECT version FROM collection")[0]["version"] == 6
