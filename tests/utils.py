import os

from pysaurus.application.application import Application
from pysaurus.database.newsql.newsql_database import NewSqlDatabase

TEST_HOME_DIR = os.path.join(os.path.dirname(__file__), "home_dir_test")
TEST_DB_FOLDER = os.path.join(
    TEST_HOME_DIR, ".Pysaurus", "databases", "test_database"
)


def get_old_app() -> Application:
    return Application(home_dir=TEST_HOME_DIR)


def get_new_sql_database() -> NewSqlDatabase:
    return NewSqlDatabase(TEST_DB_FOLDER)
