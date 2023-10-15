import os

from saurus.sql.saurus_sqlite_connection import SaurusSQLiteConnection


class VideoTermIndexDatabase(SaurusSQLiteConnection):
    __slots__ = ()
    DATABASE_SCRIPT_FILE = os.path.join(os.path.dirname(__file__), "sql_index.sql")

    def __init__(self, db_path: str):
        super().__init__(self.DATABASE_SCRIPT_FILE, db_path)
