import json
import os
from typing import Any, Iterable, Tuple

from PIL.Image import Image

from imgsimsearch.abstract_image_provider import AbstractImageProvider
from pysaurus.application.application import Application
from pysaurus.core.modules import ImageUtils
from pysaurus.database.database import Database
from pysaurus.database.db_way_def import DbWays
from pysaurus.database.thubmnail_database.thumbnail_manager import ThumbnailManager
from saurus.sql.pysaurus_program import PysaurusProgram

with open(os.path.join(os.path.dirname(__file__), "ignored/db_name.json")) as file:
    DB_INFO = json.load(file)
    DB_NAME = DB_INFO["name"]


def get_database() -> Database:
    app = Application()
    return app.open_database_from_name(DB_NAME)


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
