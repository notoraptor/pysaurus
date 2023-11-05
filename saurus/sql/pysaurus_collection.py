from typing import Collection, Dict, Iterable, List, Sequence, Tuple

from pysaurus.core.components import AbsolutePath, Date
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.db_settings import DbSettings
from pysaurus.video.lazy_video_runtime_info import (
    LazyVideoRuntimeInfo as VideoRuntimeInfo,
)
from saurus.sql.sql_old.video_entry import VideoEntry


class PysaurusCollection(AbstractDatabase):
    def set_date(self, date: Date):
        pass

    def get_settings(self) -> DbSettings:
        pass

    def get_folders(self) -> Iterable[AbsolutePath]:
        pass

    def set_folders(self, folders) -> None:
        pass

    def get_predictor(self, prop_name):
        pass

    def set_predictor(self, prop_name, theta):
        pass

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
        where: dict = None
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
