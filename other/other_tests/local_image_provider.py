from typing import Any, Iterable, List, Set, Tuple

from PIL.Image import Image

from pysaurus.core.json_backup import JsonBackup
from pysaurus.core.modules import ImageUtils
from pysaurus.core.profiling import Profiler
from pysaurus.database.db_way_def import DbWays
from pysaurus.database.jsdb.jsdbvideo.lazy_video import LazyVideo as Video
from pysaurus.database.jsdb.thubmnail_database.thumbnail_manager import ThumbnailManager
from pysaurus.imgsimsearch.abstract_image_provider import AbstractImageProvider
from saurus.sql.pysaurus_program import PysaurusProgram
from tests.utils_testing import DB_NAME


def get_db_data(db_json_path) -> List[Video]:
    json_backup = JsonBackup(db_json_path, notifier=None)
    json_dict = json_backup.load()
    assert isinstance(json_dict, dict)
    videos = sorted(
        Video(None, video_dict) for video_dict in json_dict.get("videos", ())
    )
    return videos


@Profiler.profile()
def save_similarities(
    db_json_path, similarities: List[Set[str]], prop_name="<annoy:sim>"
):
    json_backup = JsonBackup(db_json_path, notifier=None)
    json_dict = json_backup.load()
    prop_map = {
        prop_dict["n"]: prop_dict for prop_dict in json_dict.get("prop_types", ())
    }
    filename_to_video = {
        video_dict["f"]: video_dict for video_dict in json_dict.get("videos", ())
    }
    for similarity in similarities:
        for filename in similarity:
            assert filename in filename_to_video, f"Unknown video: {filename}"
    # Create property
    prop = {"n": prop_name, "d": -1, "m": False}
    # Save property
    prop_map[prop["n"]] = prop
    # Save similarities
    for i, similarity in enumerate(
        sorted(similarities, key=lambda g: len(g), reverse=True)
    ):
        for filename in similarity:
            video_dict = filename_to_video[filename]
            video_dict.setdefault("p", {})[prop_name] = [i]
    # Save data
    json_dict["prop_types"] = list(prop_map.values())
    json_dict["videos"] = list(filename_to_video.values())
    json_backup.save(json_dict)


class LocalImageProvider(AbstractImageProvider):
    __slots__ = ("ways", "thumb_manager", "nb_images", "db_name", "videos")

    def __init__(self):
        application = PysaurusProgram()
        db_name_to_path = {
            path.title: path for path in application.get_database_paths()
        }
        db_path = db_name_to_path[DB_NAME]
        self.ways = DbWays(db_path)
        videos = get_db_data(self.ways.db_json_path)
        thumb_sql_path = self.ways.db_thumb_sql_path
        assert thumb_sql_path.isfile()
        self.thumb_manager = ThumbnailManager(thumb_sql_path)
        self.nb_images = self.thumb_manager.thumb_db.query_one(
            "SELECT COUNT(filename) FROM video_to_thumbnail"
        )[0]
        self.db_name = DB_NAME
        self.videos = {video.filename.path: video for video in videos}

    def count(self) -> int:
        return self.nb_images

    def items(self) -> Iterable[Tuple[Any, Image]]:
        for row in self.thumb_manager.thumb_db.query(
            "SELECT filename, thumbnail FROM video_to_thumbnail"
        ):
            yield row["filename"], ImageUtils.from_blob(row["thumbnail"])

    def length(self, filename) -> float:
        return self.videos[filename].raw_seconds
