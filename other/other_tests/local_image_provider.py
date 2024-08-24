from typing import Any, Iterable, Tuple

from PIL.Image import Image

from other.imgsimsearch import AbstractImageProvider
from pysaurus.core.modules import ImageUtils
from pysaurus.database.db_way_def import DbWays
from pysaurus.database.jsdb.thubmnail_database import ThumbnailManager
from saurus.sql.pysaurus_program import PysaurusProgram
from tests.utils_testing import DB_NAME


class LocalImageProvider(AbstractImageProvider):
    def __init__(self):
        application = PysaurusProgram()
        db_name_to_path = {
            path.title: path for path in application.get_database_paths()
        }
        db_path = db_name_to_path[DB_NAME]
        self.ways = DbWays(db_path)
        thumb_sql_path = self.ways.db_thumb_sql_path
        assert thumb_sql_path.isfile()
        self.thumb_manager = ThumbnailManager(thumb_sql_path)
        self.nb_images = self.thumb_manager.thumb_db.query_one(
            "SELECT COUNT(filename) FROM video_to_thumbnail"
        )[0]
        self.db_name = DB_NAME

    def count(self) -> int:
        return self.nb_images

    def items(self) -> Iterable[Tuple[Any, Image]]:
        for row in self.thumb_manager.thumb_db.query(
            "SELECT filename, thumbnail FROM video_to_thumbnail"
        ):
            yield row["filename"], ImageUtils.from_blob(row["thumbnail"])
