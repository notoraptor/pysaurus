import os
import shutil

import pytest

from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.newsql.newsql_database import NewSqlDatabase
from saurus.sql.pysaurus_collection import PysaurusCollection
from saurus.sql.pysaurus_connection import PysaurusConnection
from tests.utils import (
    TEST_DB_FOLDER,
    TEST_HOME_DIR,
    get_new_sql_database,
    get_old_app,
    get_saurus_sql_database,
)

EXAMPLE_DB_NAME = "example_db_in_pysaurus"
EXAMPLE_DB_FOLDER = os.path.join(
    TEST_HOME_DIR, ".Pysaurus", "databases", EXAMPLE_DB_NAME
)


@pytest.fixture
def fake_old_app():
    return get_old_app()


@pytest.fixture
def fake_old_database(fake_old_app) -> AbstractDatabase:
    return fake_old_app.open_database_from_name("test_database")


@pytest.fixture
def fake_new_database() -> NewSqlDatabase:
    return get_new_sql_database()


@pytest.fixture
def fake_saurus_database() -> PysaurusCollection:
    return get_saurus_sql_database()


# =============================================================================
# In-memory fixtures for write tests (using temporary directories)
# =============================================================================


def _ignore_sqlite_wal_files(directory, files):
    """Ignore SQLite WAL files that may appear/disappear during copy."""
    return [f for f in files if f.endswith(("-wal", "-shm"))]


@pytest.fixture
def mem_old_database(tmp_path) -> AbstractDatabase:
    """
    JSON database loaded in a temporary directory.

    All file operations are done in a temp copy, original files are not modified.
    The temp directory is automatically cleaned up after the test.
    """
    from pysaurus.application.application import Application

    # Copy the test home directory to the temp directory
    # Ignore SQLite WAL files (-wal, -shm) which are temporary and may cause
    # race conditions when running tests in parallel with pytest-xdist
    temp_home = tmp_path / "home_dir_test"
    shutil.copytree(TEST_HOME_DIR, temp_home, ignore=_ignore_sqlite_wal_files)

    # Create Application with the temp home dir
    app = Application(home_dir=str(temp_home))
    return app.open_database_from_name("test_database")


@pytest.fixture
def mem_new_database() -> NewSqlDatabase:
    """
    NewSQL database loaded entirely in memory.

    Uses sqlite3.backup() to copy the database to memory.
    Much faster than copying files to disk.
    All operations are done in memory, original files are not modified.
    """
    return NewSqlDatabase.from_memory_copy(TEST_DB_FOLDER)


@pytest.fixture
def mem_saurus_database() -> PysaurusCollection:
    """
    Saurus SQL database loaded entirely in memory.

    Uses skullite's copy_from() to create an in-memory copy.
    All operations are done in memory, original files are not modified.
    """
    collection = PysaurusCollection(TEST_DB_FOLDER)
    memory_db = PysaurusConnection(None)
    memory_db.copy_from(collection.db)
    collection.db = memory_db
    return collection


# =============================================================================
# Fixtures for example_db_in_pysaurus (90 videos with properties)
# =============================================================================


@pytest.fixture
def example_json_database() -> AbstractDatabase:
    """JSON database from example_db_in_pysaurus (read-only, on disk)."""
    from pysaurus.application.application import Application

    app = Application(home_dir=TEST_HOME_DIR)
    return app.open_database_from_name(EXAMPLE_DB_NAME)


@pytest.fixture
def example_saurus_database() -> PysaurusCollection:
    """Saurus SQL database from example_db_in_pysaurus (read-only, on disk)."""
    return PysaurusCollection(EXAMPLE_DB_FOLDER)


@pytest.fixture
def example_json_database_memory(tmp_path) -> AbstractDatabase:
    """JSON database from example_db_in_pysaurus (in-memory copy for writes)."""
    from pysaurus.application.application import Application

    temp_home = tmp_path / "home_dir_test"
    shutil.copytree(TEST_HOME_DIR, temp_home, ignore=_ignore_sqlite_wal_files)
    app = Application(home_dir=str(temp_home))
    return app.open_database_from_name(EXAMPLE_DB_NAME)


@pytest.fixture
def example_saurus_database_memory() -> PysaurusCollection:
    """Saurus SQL database from example_db_in_pysaurus (in-memory copy for writes)."""
    collection = PysaurusCollection(EXAMPLE_DB_FOLDER)
    memory_db = PysaurusConnection(None)
    memory_db.copy_from(collection.db)
    collection.db = memory_db
    return collection
