import os

from pysaurus.application.application import Application
from pysaurus.database.newsql.newsql_database import NewSqlDatabase
from saurus.sql.pysaurus_collection import PysaurusCollection
from saurus.sql.pysaurus_connection import PysaurusConnection

TEST_HOME_DIR = os.path.join(os.path.dirname(__file__), "home_dir_test")
TEST_DB_FOLDER = os.path.join(TEST_HOME_DIR, ".Pysaurus", "databases", "test_database")


def get_old_app() -> Application:
    return Application(home_dir=TEST_HOME_DIR)


def get_new_sql_database() -> NewSqlDatabase:
    return NewSqlDatabase(TEST_DB_FOLDER)


def get_saurus_sql_database() -> PysaurusCollection:
    """
    Get a PysaurusCollection with an in-memory copy of the database.

    Uses skullite's copy_from() to create an in-memory copy,
    so the returned object can be used directly without `with` statement.
    """
    collection = PysaurusCollection(TEST_DB_FOLDER)
    memory_db = PysaurusConnection(None)
    memory_db.copy_from(collection.db)
    collection.db = memory_db
    return collection
