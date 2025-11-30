"""
Complex database algorithms that involve heavy processing or batch operations.

This class contains algorithms that:
- Iterate over multiple videos
- Perform heavy I/O operations (scanning folders, generating thumbnails)
- Execute complex multi-step processes
"""

import logging
import tempfile
from typing import Container

import ujson as json

from pysaurus.core import notifications
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.datestring import Date
from pysaurus.core.miniature import Miniature
from pysaurus.core.modules import ImageUtils
from pysaurus.core.profiling import Profiler
from pysaurus.database.algorithms.miniatures import Miniatures
from pysaurus.database.algorithms.videos import Videos
from pysaurus.video import VideoRuntimeInfo
from pysaurus.video.video_entry import VideoEntry
from saurus.language import say

logger = logging.getLogger(__name__)


class DatabaseAlgorithms:
    """Complex algorithms and batch operations."""

    __slots__ = ("db",)

    def __init__(self, db):
        """
        Initialize DatabaseAlgorithms with a database instance.

        Args:
            db: An AbstractDatabase instance
        """
        from pysaurus.database.abstract_database import AbstractDatabase

        self.db: AbstractDatabase = db

    @property
    def notifier(self):
        return self.db.notifier

    def refresh(self) -> None:
        """Update database and refresh provider."""
        self.update()
        self.db.provider.refresh()

    @Profiler.profile_method()
    def update(self) -> None:
        """Scan folders and update database with new/modified videos."""
        with self.db.to_save():
            current_date = Date.now()
            all_files = Videos.get_runtime_info_from_paths(self.db.get_folders())
            self._update_videos_not_found(all_files)
            files_to_update = self._find_video_paths_for_update(all_files)
            needing_thumbs = self._get_collectable_missing_thumbnails()
            new: list[VideoEntry] = []
            expected_thumbs: dict[str, str] = {}
            thumb_errors: dict[str, list[str]] = {}
            with tempfile.TemporaryDirectory() as tmp_dir:
                for result in Videos.hunt(files_to_update, needing_thumbs, tmp_dir):
                    task = result.task
                    filename = task.filename
                    if task.need_info and task.thumb_path:
                        if result.info and result.thumbnail:
                            # info -> new
                            # thumbnail -> expected_thumbs
                            new.append(result.info)
                            expected_thumbs[filename.path] = result.thumbnail
                        elif result.info:
                            # info + error_thumbnail -> new
                            info = result.info
                            info.errors = sorted(
                                set(info.errors) | set(result.error_thumbnail)
                            )
                            new.append(info)
                        else:
                            # unreadable + error_info -> new
                            new.append(result.get_unreadable())
                    elif task.need_info:
                        if result.info:
                            # info -> new
                            new.append(result.info)
                        else:
                            # unreadable + error_info -> new
                            new.append(result.get_unreadable())
                    else:
                        assert task.thumb_path
                        if result.thumbnail:
                            # thumbnail -> expected_thumbs
                            expected_thumbs[filename.path] = result.thumbnail
                        else:
                            # error_info + error_thumbnail -> thumb_errors
                            thumb_errors[filename.path] = sorted(
                                set(result.error_info) | set(result.error_thumbnail)
                            )

                self.db._set_date(current_date)
                if new:
                    self.db.videos_add(new, all_files)
                if expected_thumbs:
                    with Profiler(say("save thumbnails to db"), self.db.notifier):
                        self.db._thumbnails_add(expected_thumbs)

                logger.info(f"Thumbnails generated, deleting temp dir {tmp_dir}")
                # Delete thumbnail files (done at context exit)

        if thumb_errors:
            self.db.notifier.notify(notifications.VideoThumbnailErrors(thumb_errors))
        else:
            missing_thumbs = list(self._get_collectable_missing_thumbnails())
            if missing_thumbs:
                self.db.notifier.notify(notifications.MissingThumbnails(missing_thumbs))

    def _update_videos_not_found(self, existing_paths: Container[AbsolutePath]):
        """Use given container of existing paths to mark not found videos."""
        self.db.videos_set_field(
            "found",
            {
                row.video_id: (row.filename in existing_paths)
                for row in self.db.get_videos(include=["video_id", "filename"])
            },
        )

    def _find_video_paths_for_update(
        self, file_paths: dict[AbsolutePath, VideoRuntimeInfo]
    ) -> list[AbsolutePath]:
        return sorted(
            file_name
            for file_name, file_info in file_paths.items()
            if not self.db.get_videos(
                include=(),
                where={
                    "filename": file_name,
                    "mtime": file_info.mtime,
                    "file_size": file_info.size,
                    "driver_id": file_info.driver_id,
                },
            )
        )

    def _get_collectable_missing_thumbnails(self) -> list[AbsolutePath]:
        return sorted(
            video.filename
            for video in self.db.get_videos(
                include=["filename"],
                where={"readable": True, "found": True, "without_thumbnails": True},
            )
        )

    @Profiler.profile_method()
    def ensure_miniatures(self) -> list[Miniature]:
        """Generate miniatures for videos with thumbnails."""
        miniatures_path = self.db.ways.db_miniatures_path
        prev_miniatures = Miniatures.read_miniatures_file(miniatures_path)

        # Import operations for has_video
        from pysaurus.database.database_operations import DatabaseOperations

        ops = DatabaseOperations(self.db)

        valid_miniatures = {
            filename: miniature
            for filename, miniature in prev_miniatures.items()
            if ops.has_video(filename=filename)
            and ImageUtils.THUMBNAIL_SIZE == (miniature.width, miniature.height)
        }

        missing_filenames = [
            video.filename
            for video in self.db.get_videos(
                include=["filename"], where={"readable": True, "with_thumbnails": True}
            )
            if video.filename not in valid_miniatures
        ]

        added_miniatures = []
        if missing_filenames:
            tasks = [
                (video.filename, video.thumbnail)
                for video in self.db.get_videos(
                    include=("filename", "thumbnail"),
                    where={"filename": missing_filenames},
                )
            ]
            with Profiler(say("Generating miniatures."), self.db.notifier):
                added_miniatures = Miniatures.get_miniatures(tasks)

        m_dict: dict[str, Miniature] = {
            m.identifier: m
            for source in (valid_miniatures.values(), added_miniatures)
            for m in source
        }

        if len(valid_miniatures) != len(prev_miniatures) or len(added_miniatures):
            with open(miniatures_path.path, "w") as output_file:
                json.dump([m.to_dict() for m in m_dict.values()], output_file)

        self.db.notifier.notify(notifications.NbMiniatures(len(m_dict)))

        filename_to_video_id = {
            row.filename: row.video_id
            for row in self.db.get_videos(
                include=["video_id", "filename"],
                where={
                    "filename": [
                        AbsolutePath.ensure(m.identifier) for m in m_dict.values()
                    ]
                },
            )
        }
        for m in m_dict.values():
            m.video_id = filename_to_video_id[AbsolutePath.ensure(m.identifier)]
        return list(m_dict.values())

    def confirm_unique_moves(self) -> int:
        """Confirm all unique video moves."""
        unique_moves = self.get_unique_moves()
        self.move_video_entries(unique_moves)
        return len(unique_moves)

    def get_unique_moves(self) -> list[tuple[int, int]]:
        """Get list of unique video moves (1-to-1 mappings)."""
        return [
            (video_id, moves[0]["video_id"])
            for video_id, moves in self.db.videos_get_moves()
            if len(moves) == 1
        ]

    def move_video_entries(self, moves: list[tuple[int, int]]):
        """Move multiple video entries from not-found to found videos."""
        if not moves:
            return
        with self.db.to_save():
            from_indices = [move[0] for move in moves]
            to_indices = [move[1] for move in moves]
            from_map = {
                row.video_id: row
                for row in self.db.get_videos(
                    include=(
                        "video_id",
                        "similarity_id",
                        "date_entry_modified",
                        "date_entry_opened",
                        "properties",
                    ),
                    where={"video_id": from_indices, "found": False},
                )
            }
            assert all(from_id in from_map for from_id in from_indices)
            assert set(to_indices) == set(
                row.video_id
                for row in self.db.get_videos(
                    include=["video_id"], where={"video_id": to_indices, "found": True}
                )
            )
            to_properties: dict[str, dict[int, list]] = {}
            for from_id, to_id in moves:
                from_props: dict[str, list] = from_map[from_id].properties
                for prop_name, from_prop_values in from_props.items():
                    to_properties.setdefault(prop_name, {})[to_id] = from_prop_values
            # Update properties
            for prop_name, updates in to_properties.items():
                self.db.videos_tag_set(prop_name, updates, action=self.db.action.ADD)
            # Update attributes
            self.db.videos_set_field(
                "similarity_id",
                {to_id: from_map[from_id].similarity_id for from_id, to_id in moves},
            )
            self.db.videos_set_field(
                "date_entry_modified",
                {
                    to_id: from_map[from_id].date_entry_modified.time
                    for from_id, to_id in moves
                },
            )
            self.db.videos_set_field(
                "date_entry_opened",
                {
                    to_id: from_map[from_id].date_entry_opened.time
                    for from_id, to_id in moves
                },
            )
            for from_id in from_indices:
                self.db.video_entry_del(from_id)

    def move_property_values(
        self, values: list, from_name: str, to_name: str, *, concatenate=False
    ) -> int:
        """Move property values from one property to another."""
        assert self.db.get_prop_types(name=from_name, multiple=True)
        assert self.db.get_prop_types(name=to_name, with_type=str)

        from pysaurus.database.database_operations import DatabaseOperations

        ops = DatabaseOperations(self.db)

        ops.validate_prop_values(from_name, values)
        if concatenate:
            (concat_path,) = ops.validate_prop_values(
                to_name, [" ".join(str(value) for value in values)]
            )
            to_extended = [concat_path]
        else:
            to_extended = values
        path_set = set(values)
        from_new = {}
        for video_id, old_values in self.db.videos_tag_get(from_name).items():
            new_values = [v for v in old_values if v not in path_set]
            if len(old_values) > len(new_values) and (
                not concatenate or len(old_values) == len(new_values) + len(path_set)
            ):
                from_new[video_id] = new_values
        if from_new:
            self.db.videos_tag_set(from_name, from_new)
            self.db.videos_tag_set(
                to_name,
                {video_id: to_extended for video_id in from_new},
                action=self.db.action.ADD,
            )
            ops._notify_fields_modified([from_name, to_name], is_property=True)
        return len(from_new)

    def delete_property_values(self, name: str, values: list) -> None:
        """Delete property values across all videos."""
        self.db.videos_tag_set(name, {None: values}, action=self.db.action.REMOVE)

    def replace_property_values(
        self, name: str, old_values: list, new_value: object
    ) -> bool:
        """Replace property values across all videos."""
        from pysaurus.database.database_operations import DatabaseOperations

        ops = DatabaseOperations(self.db)

        modified = {}
        old_values = set(ops.validate_prop_values(name, old_values))
        (new_value,) = ops.validate_prop_values(name, [new_value])
        for video_id, previous_values in self.db.videos_tag_get(name).items():
            previous_values = set(previous_values)
            next_values = previous_values - old_values
            if len(previous_values) > len(next_values):
                next_values.add(new_value)
                modified[video_id] = next_values
        if modified:
            ops.set_property_for_videos(name, modified)
        return bool(modified)

    def fill_property_with_terms(self, prop_name: str, only_empty=False) -> None:
        """Fill property with video terms extracted from filenames."""
        from pysaurus.database.database_operations import DatabaseOperations

        ops = DatabaseOperations(self.db)

        assert self.db.get_prop_types(name=prop_name, with_type=str, multiple=True)
        old = self.db.videos_tag_get(prop_name)
        terms = self.db.videos_get_terms()
        modified = {
            video_id: video_terms
            for video_id, video_terms in terms.items()
            if not only_empty or not old.get(video_id)
        }
        if modified:
            ops.set_property_for_videos(prop_name, modified, merge=True)
