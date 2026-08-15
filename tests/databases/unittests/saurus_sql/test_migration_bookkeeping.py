"""How the migration runner records progress.

Migrations commit as they go -- skullite commits after every statement -- so
the stored version is the only record of what has actually been applied. It
must therefore advance one migration at a time, not once at the end.
"""

import sqlite3
from pathlib import Path

import pytest

from pysaurus.database.saurus import migrations
from pysaurus.database.saurus.migrations import LATEST_VERSION
from pysaurus.database.saurus.pysaurus_connection import PysaurusConnection


@pytest.fixture
def old_db_path(tmp_path) -> Path:
    """A database rolled back to version 2, so a whole chain has to run."""
    path = tmp_path / "old.db"
    PysaurusConnection(str(path))
    raw = sqlite3.connect(path)
    try:
        raw.execute("UPDATE collection SET version = 2 WHERE collection_id = 0")
        raw.commit()
    finally:
        raw.close()
    return path


def _version(path: Path) -> int:
    raw = sqlite3.connect(path)
    try:
        return raw.execute("SELECT version FROM collection").fetchone()[0]
    finally:
        raw.close()


def test_full_chain_reaches_the_latest_version(old_db_path):
    PysaurusConnection(str(old_db_path))
    assert _version(old_db_path) == LATEST_VERSION


def test_a_failure_keeps_the_migrations_that_succeeded(old_db_path, monkeypatch):
    """The stored version must match the schema actually applied.

    Recording only at the end would leave it at 2 after this failure, and the
    next run would replay m0003..m0005 over a schema they had already changed.
    """
    boom = RuntimeError("migration 5 failed")

    def explode(db):
        raise boom

    monkeypatch.setitem(migrations.MIGRATIONS, 5, explode)
    with pytest.raises(RuntimeError):
        PysaurusConnection(str(old_db_path))
    assert _version(old_db_path) == 4


def test_a_retry_resumes_where_it_stopped(old_db_path, monkeypatch):
    """After the failure is gone, only the remaining migrations run."""
    monkeypatch.setitem(
        migrations.MIGRATIONS, 5, lambda db: (_ for _ in ()).throw(RuntimeError("nope"))
    )
    with pytest.raises(RuntimeError):
        PysaurusConnection(str(old_db_path))
    monkeypatch.undo()

    applied = []
    for target, function in list(migrations.MIGRATIONS.items()):
        monkeypatch.setitem(
            migrations.MIGRATIONS,
            target,
            lambda db, t=target, f=function: (applied.append(t), f(db))[1],
        )
    PysaurusConnection(str(old_db_path))
    assert applied == list(range(5, LATEST_VERSION + 1))
    assert _version(old_db_path) == LATEST_VERSION
