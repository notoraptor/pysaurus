import logging
from typing import Collection, Dict, Iterable, List, Sequence, Tuple

from pysaurus.core.components import AbsolutePath, Date
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.path_tree import PathTree
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.db_settings import DbSettings
from pysaurus.video.lazy_video_runtime_info import (
    LazyVideoRuntimeInfo as VideoRuntimeInfo,
)
from saurus.sql.pysaurus_connection import PysaurusConnection
from saurus.sql.saurus_provider import SaurusProvider
from saurus.sql.sql_old.video_entry import VideoEntry

logger = logging.getLogger(__name__)


class PysaurusCollection(AbstractDatabase):
    __slots__ = ("db",)

    def __init__(self, path, folders=None, notifier=DEFAULT_NOTIFIER):
        super().__init__(path, SaurusProvider(self), notifier)
        self.db = PysaurusConnection(self.ways.db_sql_path.path)
        if folders:
            self.set_folders(
                set(self.get_folders())
                | {AbsolutePath.ensure(folder) for folder in folders}
            )

    def set_date(self, date: Date):
        self.db.modify("UPDATE collection SET date_updated = ?", [date.time])

    def get_settings(self) -> DbSettings:
        row = self.db.query_one(
            "SELECT miniature_pixel_distance_radius, miniature_group_min_size "
            "FROM collection"
        )
        return DbSettings.from_keys(
            miniature_pixel_distance_radius=row["miniature_pixel_distance_radius"],
            miniature_group_min_size=row["miniature_group_min_size"],
        )

    def get_folders(self) -> Iterable[AbsolutePath]:
        return [
            AbsolutePath(row["source"])
            for row in self.db.query("SELECT source FROM collection_source")
        ]

    def set_folders(self, folders) -> None:
        folders = sorted(AbsolutePath.ensure(folder) for folder in folders)
        if folders == sorted(self.get_folders()):
            return
        folders_tree = PathTree(folders)
        videos = self.db.query_all("SELECT video_id, filename FROM video")
        self.db.modify(
            "UPDATE video SET discarded = ? WHERE video_id = ?",
            [
                (
                    not folders_tree.in_folders(AbsolutePath(video["filename"])),
                    video["video_id"],
                )
                for video in videos
            ],
            many=True,
        )
        self.db.modify(
            "INSERT OR IGNORE INTO collection_source (source) VALUES (?)",
            [(path.path,) for path in folders],
            many=True,
        )

    def get_predictor(self, prop_name: str) -> List[float]:
        logger.error("get_predictor not yet implemented.")
        raise NotImplementedError()

    def set_predictor(self, prop_name: str, theta: List[float]) -> None:
        logger.error("set_predictor not yet implemented.")
        raise NotImplementedError()

    def get_prop_values(self, video_id, name):
        pass

    def update_prop_values(
        self, video_id: int, name: str, values: Collection, action: int = 0
    ):
        pass

    def get_prop_types(
        self, *, name=None, with_type=None, multiple=None, with_enum=None, default=None
    ):
        pass

    def create_prop_type(self, name, prop_type, definition, multiple):
        pass

    def remove_prop_type(self, name):
        pass

    def rename_prop_type(self, old_name, new_name):
        pass

    def convert_prop_multiplicity(self, name, multiple):
        pass

    def get_videos(
        self,
        *,
        include: Sequence[str] = None,
        with_moves: bool = False,
        where: dict = None,
    ) -> List[dict]:
        pass

    def get_video_terms(self, video_id):
        pass

    def add_video_errors(self, video_id: int, *errors: Iterable[str]) -> None:
        pass

    def change_video_entry_filename(
        self, video_id: int, path: AbsolutePath
    ) -> AbsolutePath:
        pass

    def delete_video_entry(self, video_id: int) -> None:
        pass

    def write_videos_field(self, indices: Iterable[int], field: str, values: Iterable):
        pass

    def write_new_videos(
        self,
        video_entries: List[VideoEntry],
        runtime_info: Dict[AbsolutePath, VideoRuntimeInfo],
    ) -> None:
        pass

    def open_video(self, video_id):
        pass

    def get_unique_moves(self) -> List[Tuple[int, int]]:
        pass

    def get_common_fields(self, video_indices):
        pass

    def _insert_new_thumbnails(self, filename_to_thumb_name: Dict[str, str]) -> None:
        pass
