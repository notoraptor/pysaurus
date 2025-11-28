import shutil

import pytest

from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.newsql.newsql_database import NewSqlDatabase
from tests.utils import TEST_DB_FOLDER, TEST_HOME_DIR, get_new_sql_database, get_old_app


@pytest.fixture
def fake_old_app():
    return get_old_app()


@pytest.fixture
def fake_old_database(fake_old_app) -> AbstractDatabase:
    return fake_old_app.open_database_from_name("test_database")


@pytest.fixture
def fake_new_database() -> NewSqlDatabase:
    return get_new_sql_database()


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
