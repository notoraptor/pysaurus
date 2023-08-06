import os

from saurus.sql.database import Database


class PysaurusDatabase(Database):
    __slots__ = ()

    def __init__(self, db_path: str):
        super().__init__(
            os.path.join(os.path.dirname(__file__), "database.sql"), db_path
        )
