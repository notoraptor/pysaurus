import os

import pytest

from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection
from tests.mocks.mock_database import MockDatabase
from tests.utils import TEST_HOME_DIR, get_saurus_sql_database

EXAMPLE_DB_NAME = "example_db_in_pysaurus"
EXAMPLE_DB_FOLDER = os.path.join(
    TEST_HOME_DIR, ".Pysaurus", "databases", EXAMPLE_DB_NAME
)


@pytest.fixture
def fake_saurus_database() -> PysaurusCollection:
    return get_saurus_sql_database()


@pytest.fixture
def mem_saurus_database() -> PysaurusCollection:
    # For SQL, read and write fixtures are the same,
    # since testing database is always an in-memory copy.
    return get_saurus_sql_database()


# =============================================================================
# Fixtures for example_db_in_pysaurus (90 videos with properties)
# =============================================================================


@pytest.fixture
def example_saurus_database() -> PysaurusCollection:
    """Saurus SQL database from example_db_in_pysaurus (read-only, on disk)."""
    return PysaurusCollection(EXAMPLE_DB_FOLDER)


@pytest.fixture
def example_saurus_database_memory() -> PysaurusCollection:
    """Saurus SQL database from example_db_in_pysaurus (in-memory copy for writes)."""
    return get_saurus_sql_database(EXAMPLE_DB_FOLDER)


# =============================================================================
# Mock database fixtures (fast, pure in-memory)
# =============================================================================


@pytest.fixture
def mock_database() -> MockDatabase:
    """
    Fast in-memory mock database for testing.

    Loads test data from JSON, all operations happen in memory.
    Much faster than real database fixtures - no disk I/O.
    Use this for unit tests that don't need real database implementation.
    """
    return MockDatabase.create_fresh()
