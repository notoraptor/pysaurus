import os

from saurus.sql.database import Database


class VideoTermIndexDatabase(Database):
    __slots__ = ()
    DATABASE_SCRIPT_FILE = os.path.join(os.path.dirname(__file__), "sql_index.sql")

    def __init__(self, db_path: str):
        super().__init__(self.DATABASE_SCRIPT_FILE, db_path)
