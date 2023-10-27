import logging
import tempfile
from abc import ABC, abstractmethod
from typing import Any, Container, Dict, Iterable, List, Optional, Sequence

import ujson as json

from pysaurus.application import exceptions
from pysaurus.core import functions, notifications
from pysaurus.core.components import AbsolutePath, Date, PathType
from pysaurus.core.file_utils import create_xspf_playlist
from pysaurus.core.modules import ImageUtils
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler
from pysaurus.database.algorithms.miniatures import Miniatures
from pysaurus.database.algorithms.videos import Videos
from pysaurus.database.db_settings import DbSettings
from pysaurus.database.db_way_def import DbWays
from pysaurus.miniature.miniature import Miniature
from pysaurus.video import VideoRuntimeInfo
from saurus.language import say
from saurus.sql.sql_old.video_entry import VideoEntry

logger = logging.getLogger(__name__)


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
    def set_folders(self, folders) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_folders(self) -> Iterable[AbsolutePath]:
        raise NotImplementedError()

    @abstractmethod
    def set_date(self, date: Date):
        raise NotImplementedError()

    @abstractmethod
    def read_video_field(self, video_id: int, field: str) -> Any:
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

    @abstractmethod
    def add_video_errors(self, video_id: int, *errors: Iterable[str]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_existing_thumbnails(self, filename_to_thumb_name: Dict[str, str]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def _get_collectable_missing_thumbnails(self) -> Dict[str, int]:
        raise NotImplementedError()

    @abstractmethod
    def has_video(self, **fields) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def select_videos_fields(
        self, fields: Sequence[str], *flags, **forced_flags
    ) -> Iterable[Dict[str, Any]]:
        raise NotImplementedError()

    @abstractmethod
    def get_settings(self) -> DbSettings:
        raise NotImplementedError()

    @abstractmethod
    def get_thumbnail_blob(self, filename: AbsolutePath):
        raise NotImplementedError()

    @abstractmethod
    def get_video_id(self, filename) -> int:
        raise NotImplementedError()

    @abstractmethod
    def write_videos_field(self, indices: Iterable[int], field: str, values: Iterable):
        raise NotImplementedError()

    @abstractmethod
    def write_new_videos(
        self,
        video_entries: List[VideoEntry],
        runtime_info: Dict[AbsolutePath, VideoRuntimeInfo],
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def change_video_entry_filename(
        self, video_id: int, path: AbsolutePath
    ) -> AbsolutePath:
        raise NotImplementedError()

    def count_videos(self, *flags, **forced_flags) -> int:
        return sum(1 for _ in self.select_videos_fields([], *flags, **forced_flags))

    def get_video_filename(self, video_id: int) -> AbsolutePath:
        return AbsolutePath.ensure(self.read_video_field(video_id, "filename"))

    def open_containing_folder(self, video_id: int) -> str:
        return str(self.get_video_filename(video_id).locate_file())

    def delete_video(self, video_id: int) -> AbsolutePath:
        video_filename = self.get_video_filename(video_id)
        video_filename.delete()
        self.delete_video_entry(video_id)
        return video_filename

    def to_xspf_playlist(self, video_indices: Iterable[int]) -> AbsolutePath:
        return create_xspf_playlist(map(self.get_video_filename, video_indices))

    def _notify_missing_thumbnails(self) -> None:
        remaining_thumb_videos = list(self._get_collectable_missing_thumbnails())
        self.notifier.notify(notifications.MissingThumbnails(remaining_thumb_videos))

    def _notify_fields_modified(self, fields: Sequence[str]):
        self.notifier.notify(notifications.FieldsModified(fields))

    def _notify_properties_modified(self, properties):
        self.notifier.notify(notifications.PropertiesModified(properties))

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

    @Profiler.profile_method()
    def ensure_thumbnails(self) -> None:
        # Add missing thumbnails in thumbnail manager.
        missing_thumbs = self._get_collectable_missing_thumbnails()

        expected_thumbs = {}
        thumb_errors = {}
        self.notifier.notify(
            notifications.Message(f"Missing thumbs in SQL: {len(missing_thumbs)}")
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            results = Videos.get_thumbnails(list(missing_thumbs), tmp_dir)
            for filename, result in results.items():
                if result.errors:
                    self.add_video_errors(missing_thumbs[filename], *result.errors)
                    thumb_errors[filename] = result.errors
                else:
                    expected_thumbs[filename] = result.thumbnail_path

            # Save thumbnails into thumb manager
            with Profiler(say("save thumbnails to db"), self.notifier):
                self.save_existing_thumbnails(expected_thumbs)

            logger.info(f"Thumbnails generated, deleting temp dir {tmp_dir}")
            # Delete thumbnail files (done at context exit)

        if thumb_errors:
            self.notifier.notify(notifications.VideoThumbnailErrors(thumb_errors))

    @Profiler.profile_method()
    def ensure_miniatures(self) -> List[Miniature]:
        miniatures_path = self.ways.db_miniatures_path
        prev_miniatures = Miniatures.read_miniatures_file(miniatures_path)
        valid_miniatures = {
            filename: miniature
            for filename, miniature in prev_miniatures.items()
            if self.has_video(filename=filename)
            and ImageUtils.THUMBNAIL_SIZE == (miniature.width, miniature.height)
        }

        available_videos = list(
            self.select_videos_fields(
                ["filename", "video_id"], "readable", "with_thumbnails"
            )
        )
        tasks = [
            (video["filename"], self.get_thumbnail_blob(video["filename"]))
            for video in available_videos
            if video["filename"] not in valid_miniatures
        ]

        added_miniatures = []
        if tasks:
            with Profiler(say("Generating miniatures."), self.notifier):
                added_miniatures = Miniatures.get_miniatures(tasks)

        m_dict: Dict[str, Miniature] = {
            m.identifier: m
            for source in (valid_miniatures.values(), added_miniatures)
            for m in source
        }

        settings = self.get_settings()
        Miniatures.update_group_signatures(
            m_dict,
            settings.miniature_pixel_distance_radius,
            settings.miniature_group_min_size,
        )

        if len(valid_miniatures) != len(prev_miniatures) or len(added_miniatures):
            with open(miniatures_path.path, "w") as output_file:
                json.dump([m.to_dict() for m in m_dict.values()], output_file)

        self.notifier.notify(notifications.NbMiniatures(len(m_dict)))

        for m in m_dict.values():
            m.video_id = self.get_video_id(m.identifier)
        return list(m_dict.values())

    def set_video_similarity(
        self, video_id: int, value: Optional[int], notify=True
    ) -> None:
        self.write_videos_field([video_id], "similarity_id", [value])
        if notify:
            self._notify_fields_modified(["similarity_id"])

    def change_video_file_title(self, video_id: int, new_title: str) -> None:
        if functions.has_discarded_characters(new_title):
            raise exceptions.InvalidFileName(new_title)
        old_filename: AbsolutePath = self.get_video_filename(video_id)
        if old_filename.file_title != new_title:
            self.change_video_entry_filename(
                video_id, old_filename.new_title(new_title)
            )

    def refresh(self) -> None:
        self.update()
        self.ensure_thumbnails()
        self._notify_missing_thumbnails()
        self.notifier.notify(notifications.DatabaseUpdated())
