import logging
import multiprocessing
import tempfile
from collections import Counter
from typing import Any, Callable, Dict, Iterable, List, Optional

import ujson as json

from pysaurus.application import exceptions
from pysaurus.core import functions, notifications
from pysaurus.core.components import AbsolutePath, PathType
from pysaurus.core.modules import ImageUtils
from pysaurus.core.notifying import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.profiling import Profiler
from pysaurus.database.algorithms.miniatures import Miniatures
from pysaurus.database.algorithms.videos import Videos
from pysaurus.database.json_database import JsonDatabase
from pysaurus.database.special_properties import SpecialProperties
from pysaurus.database.viewport.abstract_video_provider import AbstractVideoProvider
from pysaurus.database.viewport.video_filter import VideoFilter
from pysaurus.miniature.miniature import Miniature
from pysaurus.video_raptor.video_raptor_pyav import VideoRaptor as PythonVideoRaptor
from saurus.language import say

logger = logging.getLogger(__name__)

try:
    from pysaurus.video_raptor.video_raptor_native import VideoRaptor
except exceptions.CysaurusUnavailable:
    VideoRaptor = PythonVideoRaptor
    logger.warning("Using fallback backend for videos info and thumbnails.")


class Database(JsonDatabase):
    __slots__ = ("provider", "_initial_pid")

    def __init__(self, path, folders=None, notifier=DEFAULT_NOTIFIER):
        # type: (PathType, Iterable[PathType], Notifier) -> None
        path = AbsolutePath.ensure(path)

        self._initial_pid = multiprocessing.current_process().pid
        logger.debug(f"Loaded database {path.title} in process {self._initial_pid}")
        assert self._initial_pid is not None

        # Load database
        super().__init__(path, folders, notifier)

        # RAM data
        self.provider: Optional[AbstractVideoProvider] = VideoFilter(self)

        # Set special properties
        with Profiler(
            "install special properties", notifier=self.notifier
        ), self.to_save() as saver:
            saver.to_save = SpecialProperties.install(self)

    def __getattribute__(self, item):
        # TODO This method is for debugging, should be removed in production.
        attribute = super().__getattribute__(item)
        if callable(attribute):
            name = super().__getattribute__("get_name")()
            prev_pid = super().__getattribute__("_initial_pid")
            curr_pid = multiprocessing.current_process().pid
            assert prev_pid == curr_pid, (
                f"Database {name}: method {item} called in different processes "
                f"(expected {prev_pid}, got {curr_pid})"
            )
        return attribute

    @Profiler.profile_method()
    def ensure_thumbnails(self) -> None:
        # Remove absent videos from thumbnail manager.
        self.clean_thumbnails(
            [
                video["filename"]
                for video in self.select_videos_fields(["filename"], "readable")
            ]
        )

        # Add missing thumbnails in thumbnail manager.
        missing_thumbs = []
        for video in self.select_videos_fields(
            ["filename", "video_id"], "readable", "found"
        ):
            if not self.has_thumbnail(video["filename"]):
                missing_thumbs.append(video)

        expected_thumbs = {}
        thumb_errors = {}
        self.notifier.notify(
            notifications.Message(f"Missing thumbs in SQL: {len(missing_thumbs)}")
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            filename_to_video = {
                video["filename"].path: video for video in missing_thumbs
            }
            results = Videos.get_thumbnails(
                [video["filename"] for video in missing_thumbs], tmp_dir
            )
            for filename, result in results.items():
                if result.errors:
                    self.add_video_errors(
                        filename_to_video[filename]["video_id"], *result.errors
                    )
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
        self._notify_missing_thumbnails()
        self.notifier.notify(notifications.DatabaseUpdated())

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

        Miniatures.update_group_signatures(
            m_dict,
            self.settings.miniature_pixel_distance_radius,
            self.settings.miniature_group_min_size,
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
        self.write_video_fields(video_id, similarity_id=value)
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

    def reopen(self):
        pass

    def refresh(self) -> None:
        self.update()
        self.ensure_thumbnails()

    def delete_property_value(self, name: str, values: list) -> None:
        self.__del_prop_val(self.get_all_video_indices(), name, values)

    def move_property_value(self, old_name: str, values: list, new_name: str) -> None:
        modified = self.__del_prop_val(self.get_all_video_indices(), old_name, values)
        for video_id in modified:
            self.merge_prop_values(video_id, new_name, values)
        if modified:
            self._notify_properties_modified([old_name, new_name])

    def __del_prop_val(
        self, video_indices: Iterable[int], name: str, values: list
    ) -> List[int]:
        modified = []
        values = set(self.validate_prop_values(name, values))
        for video_id in video_indices:
            previous_values = set(self.get_prop_values(video_id, name))
            new_values = previous_values - values
            if len(previous_values) > len(new_values):
                self.set_prop_values(video_id, name, new_values)
                modified.append(video_id)
        if modified:
            self._notify_properties_modified([name])
        return modified

    def edit_property_value(
        self, name: str, old_values: list, new_value: object
    ) -> bool:
        modified = []
        old_values = set(self.validate_prop_values(name, old_values))
        (new_value,) = self.validate_prop_values(name, [new_value])
        for video_id in self.get_all_video_indices():
            previous_values = set(self.get_prop_values(video_id, name))
            next_values = previous_values - old_values
            if len(previous_values) > len(next_values):
                next_values.add(new_value)
                self.set_prop_values(video_id, name, next_values)
                modified.append(video_id)
        if modified:
            self._notify_properties_modified([name])
        return bool(modified)

    def edit_property_for_videos(
        self,
        video_indices: List[int],
        name: str,
        values_to_add: list,
        values_to_remove: list,
    ) -> None:
        print(
            "Edit",
            len(video_indices),
            "video props, add",
            values_to_add,
            "remove",
            values_to_remove,
        )
        values_to_add = set(self.validate_prop_values(name, values_to_add))
        values_to_remove = set(self.validate_prop_values(name, values_to_remove))
        for video_id in video_indices:
            values = (
                set(self.get_prop_values(video_id, name)) - values_to_remove
            ) | values_to_add
            self.set_prop_values(video_id, name, values)
        self._notify_properties_modified([name])

    def count_property_values(self, video_indices: List[int], name: str) -> List[List]:
        count = Counter()
        for video_id in video_indices:
            count.update(self.get_prop_values(video_id, name))
        return sorted(list(item) for item in count.items())

    def fill_property_with_terms(self, prop_name: str, only_empty=False) -> None:
        assert self.has_prop_type(prop_name, with_type=str, multiple=True)
        modified = []
        for video_id in self.get_all_video_indices():
            values = self.get_prop_values(video_id, prop_name)
            if only_empty and values:
                continue
            self.set_prop_values(
                video_id, prop_name, values + self.get_video_terms(video_id)
            )
            modified.append(video_id)
        if modified:
            self._notify_properties_modified([prop_name])

    def prop_to_lowercase(self, prop_name) -> None:
        return self._edit_prop_value(prop_name, lambda value: value.strip().lower())

    def prop_to_uppercase(self, prop_name) -> None:
        return self._edit_prop_value(prop_name, lambda value: value.strip().upper())

    def _edit_prop_value(self, prop_name: str, function: Callable[[Any], Any]) -> None:
        assert self.has_prop_type(prop_name, with_type=str)
        modified = []
        for video_id in self.get_all_video_indices():
            values = self.get_prop_values(video_id, prop_name)
            new_values = [function(value) for value in values]
            if values and new_values != values:
                self.set_prop_values(video_id, prop_name, new_values)
                modified.append(video_id)
        if modified:
            self._notify_properties_modified([prop_name])

    def move_concatenated_prop_val(
        self, path: list, from_property: str, to_property: str
    ) -> int:
        assert self.has_prop_type(from_property, multiple=True)
        assert self.has_prop_type(to_property, with_type=str)
        self.validate_prop_values(from_property, path)
        (concat_path,) = self.validate_prop_values(
            to_property, [" ".join(str(value) for value in path)]
        )
        modified = []
        path_set = set(path)
        for video_id in self.get_all_video_indices():
            old_values = self.get_prop_values(video_id, from_property)
            new_values = [v for v in old_values if v not in path_set]
            if len(old_values) == len(new_values) + len(path_set):
                self.set_prop_values(video_id, from_property, new_values)
                self.merge_prop_values(video_id, to_property, [concat_path])
                modified.append(video_id)
        if modified:
            self._notify_properties_modified([from_property, to_property])
        return len(modified)
