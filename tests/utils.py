import os
import sqlite3
from pathlib import Path

from pysaurus.database.saurus.pysaurus_collection import DB_SQL_PATH, PysaurusCollection
from pysaurus.database.saurus.pysaurus_connection import PysaurusConnection

TEST_HOME_DIR = os.path.join(os.path.dirname(__file__), "home_dir_test")
TEST_DB_FOLDER = os.path.join(TEST_HOME_DIR, ".Pysaurus", "databases", "test_database")


class _InMemoryPysaurusCollection(PysaurusCollection):
    """A PysaurusCollection whose on-disk source is read only.

    Production ``PysaurusCollection._open_db()`` opens the database read-write and
    writes to it on open (a ``name`` sync, plus migration/schema replay inside
    ``PysaurusConnection.__init__``). Pointing many xdist workers at the *same*
    shared on-disk test fixture makes those writes race, raising intermittently::

        sqlite3.OperationalError: attempt to write a readonly database

    This test-only subclass opens the source read-only instead (SQLite
    ``immutable=1``, which also skips all file locking) and copies it into an
    in-memory database. The shared fixture file is therefore never written, and
    every worker gets its own isolated, fully writable copy. Migration and schema
    replay then run on the *in-memory copy*, mirroring the production
    "open an existing database" path so the fixture stays correct even if
    ``database.sql`` advances past the committed fixture's version.
    """

    __slots__ = ()

    def _open_db(self) -> None:
        source_uri = (
            Path(self.ways.get_path(DB_SQL_PATH).path).as_uri() + "?immutable=1"
        )
        source = sqlite3.connect(source_uri, uri=True)
        try:
            self.db = PysaurusConnection(None)  # fresh in-memory database
            with self.db.connect() as target:
                source.backup(target.connection)  # overwrite it with the on-disk data
        finally:
            source.close()
        # Same steps as opening an existing database, but on the in-memory copy:
        # bring the schema up to date, then sync the name from the folder.
        self.db._migrate()
        self.db._run_schema_script()
        self.db.modify(
            "UPDATE collection SET name = ? WHERE collection_id = 0", [self.get_name()]
        )


def get_saurus_sql_database(folder: str = TEST_DB_FOLDER) -> PysaurusCollection:
    """Get a PysaurusCollection with an in-memory copy of the on-disk database.

    The on-disk source is opened read-only (immutable), so concurrent xdist
    workers never write to the shared test fixture. The returned object is a
    fully writable in-memory database.
    """
    return _InMemoryPysaurusCollection(folder)
