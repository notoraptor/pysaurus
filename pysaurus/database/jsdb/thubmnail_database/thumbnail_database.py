import os

from saurus.sql.saurus_sqlite_database import SaurusSQLiteDatabase


class ThumbnailDatabase(SaurusSQLiteDatabase):
    __slots__ = ()
    DATABASE_SCRIPT_FILE = os.path.join(os.path.dirname(__file__), "thumbnail_db.sql")

    def __init__(self, db_path: str):
        super().__init__(db_path, script_path=self.DATABASE_SCRIPT_FILE)
