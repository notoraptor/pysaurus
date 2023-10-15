import os

from saurus.sql.saurus_sqlite_connection import SaurusSQLiteConnection


class PysaurusDatabase(SaurusSQLiteConnection):
    __slots__ = ()

    def __init__(self, db_path: str):
        super().__init__(
            os.path.join(os.path.dirname(__file__), "database.sql"), db_path
        )
