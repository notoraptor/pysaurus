from abc import ABC, abstractmethod
from typing import Container, Dict, Iterable, List

from pysaurus.core import notifications
from pysaurus.core.components import AbsolutePath, Date, PathType
from pysaurus.core.file_utils import create_xspf_playlist
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler
from pysaurus.database.algorithms.videos import Videos
from pysaurus.database.db_way_def import DbWays
from pysaurus.video import VideoRuntimeInfo
from saurus.sql.sql_old.video_entry import VideoEntry


class AbstractDatabase(ABC):
    __slots__ = ("ways", "notifier")

    def __init__(self, db_folder: PathType, notifier=DEFAULT_NOTIFIER):
        db_folder = AbsolutePath.ensure_directory(db_folder)
        self.ways = DbWays(db_folder)
        self.notifier = notifier

    def rename(self, new_name: str) -> None:
        self.ways = self.ways.renamed(new_name)

    def get_name(self) -> str:
        return self.ways.db_folder.title

    @abstractmethod
    def get_folders(self) -> Iterable[AbsolutePath]:
        raise NotImplementedError()

    @abstractmethod
    def set_date(self, date: Date):
        raise NotImplementedError()

    @abstractmethod
    def get_video_filename(self, video_id: int) -> AbsolutePath:
        raise NotImplementedError()

    @abstractmethod
    def delete_video_entry(self, video_id: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def _update_videos_not_found(self, existing_paths: Container[AbsolutePath]):
        """Use given container of existing paths to mark not found videos."""
        raise NotImplementedError()

    @abstractmethod
    def _find_video_paths_for_update(
        self, file_paths: Dict[AbsolutePath, VideoRuntimeInfo]
    ) -> List[str]:
        raise NotImplementedError()

    def write_new_videos(
        self,
        video_entries: List[VideoEntry],
        runtime_info: Dict[AbsolutePath, VideoRuntimeInfo],
    ) -> None:
        raise NotImplementedError()

    def open_containing_folder(self, video_id: int) -> str:
        return str(self.get_video_filename(video_id).locate_file())

    def delete_video(self, video_id: int) -> AbsolutePath:
        video_filename = self.get_video_filename(video_id)
        video_filename.delete()
        self.delete_video_entry(video_id)
        return video_filename

    def to_xspf_playlist(self, video_indices: Iterable[int]) -> AbsolutePath:
        return create_xspf_playlist(map(self.get_video_filename, video_indices))

    @Profiler.profile_method()
    def update(self) -> None:
        current_date = Date.now()
        all_files = Videos.get_runtime_info_from_paths(self.get_folders())
        self._update_videos_not_found(all_files)
        files_to_update = self._find_video_paths_for_update(all_files)
        if files_to_update:
            new = Videos.get_info_from_filenames(files_to_update)
            self.set_date(current_date)
            self.write_new_videos(new, all_files)
            self.notifier.notify(notifications.DatabaseUpdated())
