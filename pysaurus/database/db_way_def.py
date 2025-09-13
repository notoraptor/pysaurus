from pysaurus.core.absolute_path import PathType
from pysaurus.database.db_paths import DatabasePaths

DB_JSON_PATH = ("json_path", "json")
DB_LOG_PATH = ("log_path", "log")
DB_THUMB_SQL_PATH = ("thumb_sql_path", "thumbnails.sql.db")
DB_MINIATURES_PATH = ("miniatures_path", "miniatures.json")
DB_INDEX_PKL_PATH = ("index_pkl_path", "index.pkl")
DB_SQL_PATH = ("sql_path", "full.db")


class DbWays(DatabasePaths):
    __slots__ = ()

    def __init__(self, folder: PathType):
        super().__init__(folder)
        self.define(DB_JSON_PATH)
        self.define(DB_LOG_PATH)
        self.define(DB_THUMB_SQL_PATH)
        self.define(DB_MINIATURES_PATH)
        self.define(DB_INDEX_PKL_PATH)
        self.define(DB_SQL_PATH)

    @property
    def db_json_path(self):
        return self.get(DB_JSON_PATH)

    @property
    def db_log_path(self):
        return self.get(DB_LOG_PATH)

    @property
    def db_thumb_sql_path(self):
        return self.get(DB_THUMB_SQL_PATH)

    @property
    def db_miniatures_path(self):
        return self.get(DB_MINIATURES_PATH)

    @property
    def db_index_pkl_path(self):
        return self.get(DB_INDEX_PKL_PATH)

    @property
    def db_sql_path(self):
        return self.get(DB_SQL_PATH)
