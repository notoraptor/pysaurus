"""Migration m0006 normalizes the mount point of every stored path.

A database written before the rule can hold one file under two spellings of
its drive, which never compare equal: the folder scan reports indexed videos
as unknown, and the "disk" grouping splits in two.
"""

import os
import sqlite3
from pathlib import Path

import pytest

from pysaurus.application.exceptions import MountPointCaseConflict
from pysaurus.database.saurus.migrations import LATEST_VERSION
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
    """One file under both spellings, plus a clean row the refusal must spare."""
    return _legacy_db(
        tmp_path / "conflict.db",
        [
            ("C:\\Videos\\a.mkv", "C:\\"),
            ("c:\\Videos\\a.mkv", "c:\\"),
            ("c:\\Videos\\clean.mkv", "c:\\"),
        ],
    )


@windows_only
def test_a_conflict_refuses_the_migration(conflict_db_path):
    """Merging needs the application, so the migration will not pick a winner."""
    with pytest.raises(MountPointCaseConflict) as excinfo:
        PysaurusConnection(str(conflict_db_path))
    assert set(excinfo.value.args) == {"C:\\Videos\\a.mkv", "c:\\Videos\\a.mkv"}


@windows_only
def test_a_refusal_writes_nothing(conflict_db_path):
    """The check runs before any UPDATE, so the database is left as it was.

    Version included: skullite commits per statement, so a half-applied
    migration would be recorded as done.
    """
    with pytest.raises(MountPointCaseConflict):
        PysaurusConnection(str(conflict_db_path))
    raw = sqlite3.connect(conflict_db_path)
    try:
        assert raw.execute("SELECT version FROM collection").fetchone()[0] == 5
        stored = sorted(row[0] for row in raw.execute("SELECT filename FROM video"))
    finally:
        raw.close()
    assert stored == ["C:\\Videos\\a.mkv", "c:\\Videos\\a.mkv", "c:\\Videos\\clean.mkv"]


@windows_only
def test_a_refusal_repeats_on_every_open(conflict_db_path):
    """Nothing is silently swallowed: the base stays visibly unmigrated."""
    for _ in range(2):
        with pytest.raises(MountPointCaseConflict):
            PysaurusConnection(str(conflict_db_path))


def test_migration_is_idempotent(legacy_db_path):
    PysaurusConnection(str(legacy_db_path))
    db = PysaurusConnection(str(legacy_db_path))  # second open: nothing left to do
    assert (
        db.query_all("SELECT version FROM collection")[0]["version"] == LATEST_VERSION
    )
    assert len(_filenames(db)) == 3


def test_fresh_database_is_at_the_latest_version(tmp_path):
    db = PysaurusConnection(str(tmp_path / "fresh.db"))
    assert (
        db.query_all("SELECT version FROM collection")[0]["version"] == LATEST_VERSION
    )
