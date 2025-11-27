import pytest

from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.newsql.newsql_database import NewSqlDatabase
from tests.utils import get_new_sql_database, get_old_app


@pytest.fixture
def fake_old_app():
    return get_old_app()


@pytest.fixture
def fake_old_database(fake_old_app) -> AbstractDatabase:
    return fake_old_app.open_database_from_name("test_database")


@pytest.fixture
def fake_new_database() -> NewSqlDatabase:
    return get_new_sql_database()
