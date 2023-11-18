import logging
import tempfile
from multiprocessing import Pool
from typing import Container, Dict, List

from pysaurus.core import notifications
from pysaurus.core.components import AbsolutePath
from pysaurus.core.job_notifications import notify_job_start
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.video import VideoRuntimeInfo
from pysaurus.video_raptor.video_raptor_pyav import VideoRaptor
from saurus.language import say
from saurus.sql.pysaurus_connection import PysaurusConnection

logger = logging.getLogger(__name__)


class OldPysaurusCollection(AbstractDatabase):
    __slots__ = ("db",)

    def __init__(self, path, folders=None, notifier=DEFAULT_NOTIFIER):
        super().__init__(path, None, notifier)
        self.db = PysaurusConnection(self.ways.db_sql_path.path)
        self._load(folders)

    def _load(self, folders=None):
        if folders:
            new_folders = [AbsolutePath.ensure(path) for path in folders]
            old_folders = set(self.get_folders())
            folders_to_add = [
                (path.path,) for path in new_folders if path not in old_folders
            ]
            if folders_to_add:
                self.db.modify(
                    "INSERT INTO collection_source (source) VALUES (?)",
                    folders_to_add,
                    many=True,
                )
                logger.info(f"Added {len(folders_to_add)} new source(s).")
                # Update discarded videos.
                # Newly added folders can only un-discard previously discarded videos.
                source_tree = PathTree(list(old_folders) + list(new_folders))
                rows = self.db.query_all(
                    "SELECT video_id, filename FROM video WHERE discarded = 1"
                )
                allowed = [
                    row
                    for row in rows
                    if source_tree.in_folders(AbsolutePath(row["filename"]))
                ]
                if allowed:
                    self.db.modify(
                        "UPDATE video SET discarded = 0 WHERE video_id = ?",
                        [[row["video_id"]] for row in allowed],
                        many=True,
                    )
                    logger.info(f"Un-discarded {len(allowed)} video(s).")

    def ensure_thumbnails(self) -> None:
        # super().ensure_thumbnails()
        # Get missing thumbs.
        filename_to_video = {
            row["filename"]: row
            for row in self.db.query(
                "SELECT video_id, filename FROM video "
                "WHERE discarded = 0 AND unreadable = 0 AND is_file = 1"
            )
        }
        missing_thumbs = sorted(
            row["filename"]
            for row in self.db.query(
                "SELECT filename FROM video WHERE "
                "discarded = 0 AND unreadable = 0 AND is_file = 1 AND video_id NOT IN "
                "(SELECT video_id FROM video_thumbnail)"
            )
        )
        # Generate new thumbs.
        thumb_errors = {}
        self.notifier.notify(
            notifications.Message(f"Missing thumbs in SQL: {len(missing_thumbs)}")
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Generate thumbnail filenames as long as tasks
            tasks = [
                (
                    self.notifier,
                    i,
                    filename,
                    AbsolutePath.file_path(tmp_dir, i, "jpg").path,
                )
                for i, filename in enumerate(missing_thumbs)
            ]
            # Generate thumbnail files
            expected_thumbs = {
                filename: thumb_path for _, _, filename, thumb_path in tasks
            }
            raptor = VideoRaptor()
            with Profiler(say("Generate thumbnail files"), self.notifier):
                notify_job_start(
                    self.notifier, raptor.run_thumbnail_task, len(tasks), "thumbnails"
                )
                with Pool() as p:
                    errors = list(p.starmap(raptor.run_thumbnail_task, tasks))
            video_errors = []
            for err in errors:
                if err:
                    del expected_thumbs[err["filename"]]
                    video = filename_to_video[err["filename"]]
                    video_errors.extend(
                        (video["video_id"], verr) for verr in err["errors"]
                    )
                    thumb_errors[err["filename"]] = err["errors"]
            self.db.modify(
                "INSERT OR IGNORE INTO video_error (video_id, error) VALUES (?, ?)",
                video_errors,
                many=True,
            )
            # Save thumbnails into thumb manager
            with Profiler(say("save thumbnails to db"), self.notifier):
                self.db.modify(
                    "INSERT OR IGNORE INTO video_thumbnail "
                    "(video_id, thumbnail) VALUES (?, ?)",
                    [
                        (
                            filename_to_video[filename]["video_id"],
                            AbsolutePath(thumb_path).read_binary_file(),
                        )
                        for filename, thumb_path in expected_thumbs.items()
                    ],
                    many=True,
                )
            logger.info(f"Thumbnails generated, deleting temp dir {tmp_dir}")
            # Delete thumbnail files (done at context exit)

        if thumb_errors:
            self.notifier.notify(notifications.VideoThumbnailErrors(thumb_errors))
        self._notify_missing_thumbnails()
        self.provider.refresh()

    def _update_videos_not_found(self, existing_paths: Container[AbsolutePath]):
        # super()._update_videos_not_found(existing_paths)
        rows = self.db.query_all(
            "SELECT video_id, filename FROM video WHERE discarded = 0"
        )
        self.db.modify(
            "UPDATE video SET is_file = ? WHERE video_id = ?",
            [
                (AbsolutePath(row["filename"]) in existing_paths, row["video_id"])
                for row in rows
            ],
            many=True,
        )

    def _find_video_paths_for_update(
        self, file_paths: Dict[AbsolutePath, VideoRuntimeInfo]
    ) -> List[str]:
        # return super()._find_video_paths_for_update(file_paths)
        all_file_names = []
        available = {
            AbsolutePath(row["filename"]): row
            for row in self.db.query(
                "SELECT "
                "filename, mtime, file_size, driver_id, "
                "unreadable, audio_codec, audio_bits "
                "FROM video WHERE discarded = 0"
            )
        }
        for file_name, file_info in file_paths.items():
            video: dict = available.get(file_name)
            if (
                video is None
                or file_info.mtime != video["mtime"]
                or file_info.size != video["file_size"]
                or file_info.driver_id != video["driver_id"]
                or self._video_must_be_updated(video)
            ):
                all_file_names.append(file_name.standard_path)
        all_file_names.sort()
        return all_file_names

    @classmethod
    def _video_must_be_updated(cls, video: dict):
        # A video readable with existing audio stream must have valid audio bits
        # return super()._video_must_be_updated(video)
        return (
            not video["unreadable"] and video["audio_codec"] and not video["audio_bits"]
        )
