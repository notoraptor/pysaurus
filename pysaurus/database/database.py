import logging
import os
from collections import Counter
from typing import Any, Callable, Dict, Iterable, List, Optional, Set

import ujson as json

from pysaurus.application import exceptions
from pysaurus.application.language.default_language import DefaultLanguage
from pysaurus.core import functions, notifications
from pysaurus.core.components import (
    AbsolutePath,
    Date,
    PathType,
)
from pysaurus.core.constants import JPEG_EXTENSION, THUMBNAIL_EXTENSION
from pysaurus.core.functions import generate_temp_file_path
from pysaurus.core.job_notifications import notify_job_progress, notify_job_start
from pysaurus.core.modules import FileSystem, ImageUtils
from pysaurus.core.notifying import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.parallelization import parallelize, run_split_batch
from pysaurus.core.profiling import Profiler
from pysaurus.database import jobs_python
from pysaurus.database.db_paths import DbPaths
from pysaurus.database.jobs_python import compress_thumbnails_to_jpeg
from pysaurus.database.json_database import JsonDatabase
from pysaurus.database.special_properties import SpecialProperties
from pysaurus.database.viewport.abstract_video_provider import AbstractVideoProvider
from pysaurus.database.viewport.video_filter import VideoFilter
from pysaurus.miniature.group_computer import GroupComputer
from pysaurus.miniature.miniature import Miniature
from pysaurus.video import Video
from pysaurus.video.video_indexer import VideoIndexer
from saurus.language import say

logger = logging.getLogger(__name__)

try:
    from pysaurus.video_raptor.video_raptor_native import VideoRaptor
except exceptions.CysaurusUnavailable:
    from pysaurus.video_raptor.video_raptor_pyav import VideoRaptor

    logger.warning("Using fallback backend for videos info and thumbnails.")


class Database(JsonDatabase):
    __slots__ = ("__paths", "lang", "provider")

    def __init__(self, path, folders=None, notifier=None, lang=None):
        # type: (PathType, Iterable[PathType], Notifier, DefaultLanguage) -> None
        # Paths
        self.__paths = DbPaths(path)
        # RAM data
        self.lang = lang or DefaultLanguage
        # self.provider: Optional[AbstractVideoProvider] = VideoSelector(self)
        self.provider: Optional[AbstractVideoProvider] = VideoFilter(self)
        # Set log file
        notifier = notifier or DEFAULT_NOTIFIER
        notifier.set_log_path(self.__paths.log_path.path)
        # Load database
        super().__init__(
            self.__paths.json_path,
            folders,
            notifier,
            indexer=VideoIndexer(notifier),
        )
        # Set special properties
        with Profiler(
            "install special properties", notifier=self.notifier
        ), self.to_save() as saver:
            saver.to_save = SpecialProperties.install(self)
        self.compress_thumbnails()

    # Properties.

    name = property(lambda self: self.__paths.db_folder.title)
    thumbnail_folder = property(lambda self: self.__paths.thumb_folder)

    # Private methods.

    def __check_thumbnails_on_disk(self):
        # type: () -> Dict[str, Date]
        thumbs = {}
        with Profiler(say("Collect thumbnails"), self.notifier):
            for entry in FileSystem.scandir(
                self.__paths.thumb_folder.path
            ):  # type: os.DirEntry
                if entry.path.lower().endswith(f".{JPEG_EXTENSION}"):
                    name = entry.name
                    thumbs[name[: -(len(JPEG_EXTENSION) + 1)]] = Date(
                        entry.stat().st_mtime
                    )
        return thumbs

    def _clean_thumbnails(self, thumb_names: List[str]):
        notify_job_start(
            self.notifier, self._clean_thumbnails, len(thumb_names), "thumbnails"
        )
        for i, thumb_name in enumerate(thumb_names):
            png_path = AbsolutePath.file_path(
                self.__paths.thumb_folder, thumb_name, THUMBNAIL_EXTENSION
            )
            jpg_path = AbsolutePath.file_path(
                self.__paths.thumb_folder, thumb_name, JPEG_EXTENSION
            )
            png_deleted = False
            jpg_deleted = False
            if png_path.isfile():
                png_path.delete()
                assert not png_path.isfile()
                png_deleted = True
            if jpg_path.isfile():
                jpg_path.delete()
                assert not jpg_path.isfile()
                jpg_deleted = True
            assert png_deleted or jpg_deleted
            notify_job_progress(
                self.notifier, self._clean_thumbnails, None, i + 1, len(thumb_names)
            )

    # Public methods.

    @Profiler.profile_method()
    def update(self) -> None:
        current_date = Date.now()

        all_files = jobs_python.collect_video_paths(self.video_folders, self.notifier)
        self._update_videos_not_found(all_files)
        files_to_update = self._find_video_paths_for_update(all_files)
        if not files_to_update:
            return

        backend_raptor = VideoRaptor()
        with Profiler(
            say("Collect videos info"),
            notifier=self.notifier,
        ):
            notify_job_start(
                self.notifier,
                backend_raptor.collect_video_info,
                len(files_to_update),
                "videos",
            )
            results = list(
                run_split_batch(
                    backend_raptor.collect_video_info,
                    files_to_update,
                    extra_args=[self.__paths.db_folder, self.notifier],
                )
            )

        new: List[dict] = [
            Video.ensure_short_keys(d, backend_raptor.RETURNS_SHORT_KEYS)
            for arr in results
            for d in arr
        ]
        assert len(files_to_update) == len(new)

        if new:
            self.set_date(current_date)
            self.write_new_videos(new, all_files)
            self.notifier.notify(notifications.DatabaseUpdated())

    @Profiler.profile_method()
    def ensure_thumbnails(self) -> None:
        valid_thumb_names: Set[str] = set()
        videos_without_thumbs: List[dict] = []
        thumb_to_videos: Dict[str, List[dict]] = {}
        thumb_errors: Dict[str, List[str]] = {}

        # Collect videos with and without thumbnails.
        existing_thumb_names = self.__check_thumbnails_on_disk()

        with Profiler(say("Check videos thumbnails"), notifier=self.notifier):
            for video in self.select_videos_fields(
                [
                    "date",
                    "filename",
                    "found",
                    "thumb_name",
                    "unreadable_thumbnail",
                    "video_id",
                ],
                "readable",
            ):
                thumb_name = video["thumb_name"]
                if not video["found"]:
                    if thumb_name in existing_thumb_names:
                        self.write_video_field(
                            video["video_id"],
                            "has_runtime_thumbnail",
                            True,
                        )
                        valid_thumb_names.add(thumb_name)
                elif not video["unreadable_thumbnail"]:
                    if (
                        thumb_name in existing_thumb_names
                        and existing_thumb_names[thumb_name] > video["date"]
                    ):
                        thumb_to_videos.setdefault(thumb_name, []).append(video)
                    else:
                        videos_without_thumbs.append(video)

        # If a thumbnail name is associated to many videos,
        # consider these videos don't have thumbnails.
        with Profiler(say("Check unique thumbnails"), notifier=self.notifier):
            for valid_thumb_name, vds in thumb_to_videos.items():
                if len(vds) == 1:
                    video: dict = vds[0]
                    valid_thumb_names.add(valid_thumb_name)
                    self.write_video_field(
                        video["video_id"], "has_runtime_thumbnail", True
                    )
                else:
                    videos_without_thumbs.extend(vds)
        nb_videos_no_thumbs = len(videos_without_thumbs)
        del thumb_to_videos

        thumbs_to_clean = [
            thumb_name
            for thumb_name in existing_thumb_names
            if thumb_name not in valid_thumb_names
        ]
        if thumbs_to_clean:
            self.notifier.notify(
                notifications.Message(
                    f"Valid thumbnails before ensuring: "
                    f"{len(valid_thumb_names)} / {len(existing_thumb_names)}, "
                    f"to clean {len(thumbs_to_clean)}"
                )
            )
            assert valid_thumb_names or not self.query()
            self._clean_thumbnails(thumbs_to_clean)

        if not videos_without_thumbs:
            self._notify_missing_thumbnails()
            return

        for video in videos_without_thumbs:
            base_thumb_name = video["thumb_name"]
            thumb_name_index = 0
            thumb_name = base_thumb_name
            while thumb_name in valid_thumb_names:
                thumb_name = f"{base_thumb_name}_{thumb_name_index}"
                thumb_name_index += 1
            self.write_video_fields(
                video["video_id"], thumb_name=thumb_name, has_runtime_thumbnail=True
            )
            valid_thumb_names.add(thumb_name)
        del valid_thumb_names

        backend_raptor = VideoRaptor()
        with Profiler(
            title=say(
                "Get thumbnails from JSON",
            ),
            notifier=self.notifier,
        ):
            notify_job_start(
                self.notifier,
                backend_raptor.collect_video_thumbnails,
                nb_videos_no_thumbs,
                "videos",
            )
            results = list(
                run_split_batch(
                    backend_raptor.collect_video_thumbnails,
                    [
                        (video["filename"].path, video["thumb_name"])
                        for video in videos_without_thumbs
                    ],
                    extra_args=[
                        self.__paths.db_folder,
                        self.__paths.thumb_folder.best_path,
                        self.notifier,
                    ],
                )
            )

        for arr in results:
            for d in arr:
                d = Video.ensure_short_keys(d, backend_raptor.RETURNS_SHORT_KEYS)
                assert len(d) == 2 and "f" in d and "e" in d
                file_name = d["f"]
                file_path = AbsolutePath.ensure(file_name)
                thumb_errors[file_name] = d["e"]
                video_id = self.get_video_id(file_path)
                self.write_video_fields(
                    video_id,
                    unreadable_thumbnail=True,
                    has_runtime_thumbnail=False,
                )

        if thumb_errors:
            self.notifier.notify(notifications.VideoThumbnailErrors(thumb_errors))

        self.compress_thumbnails()
        self._notify_missing_thumbnails()
        self.notifier.notify(notifications.DatabaseUpdated())

    @Profiler.profile_method()
    def ensure_miniatures(self, returns=False) -> Optional[List[Miniature]]:
        identifiers = set()  # type: Set[AbsolutePath]
        valid_dictionaries = []
        added_miniatures = []
        have_removed = False
        have_added = False

        if self.__paths.miniatures_path.exists():
            with open(
                self.__paths.miniatures_path.assert_file().path
            ) as miniatures_file:
                json_array = json.load(miniatures_file)
            if not isinstance(json_array, list):
                raise exceptions.InvalidMiniaturesJSON(self.__paths.miniatures_path)
            for dct in json_array:
                identifier = AbsolutePath(dct["i"])
                if self.has_video(identifier) and ImageUtils.DEFAULT_THUMBNAIL_SIZE == (
                    dct["w"],
                    dct["h"],
                ):
                    identifiers.add(identifier)
                    valid_dictionaries.append(dct)
            have_removed = len(valid_dictionaries) != len(json_array)
            del json_array

        available_videos = list(
            self.select_videos_fields(
                ["filename", "thumbnail_path", "video_id"],
                "readable",
                "with_thumbnails",
            )
        )
        tasks = [
            (video["filename"], video["thumbnail_path"])
            for video in available_videos
            if video["filename"] not in identifiers
        ]

        if tasks:
            have_added = True
            with Profiler(say("Generating miniatures."), self.notifier):
                notify_job_start(
                    self.notifier,
                    jobs_python.generate_video_miniatures,
                    len(tasks),
                    "videos",
                )
                results = list(
                    run_split_batch(
                        jobs_python.generate_video_miniatures,
                        tasks,
                        extra_args=[self.notifier],
                    )
                )
            for local_array in results:
                added_miniatures.extend(local_array)
            del results

        valid_miniatures = [Miniature.from_dict(d) for d in valid_dictionaries]
        available_miniatures = valid_miniatures + added_miniatures
        m_dict = {
            m.identifier: m for m in available_miniatures
        }  # type: Dict[str, Miniature]

        m_no_groups = [
            m
            for m in valid_miniatures
            if not m.has_group_signature(
                self.settings.miniature_pixel_distance_radius,
                self.settings.miniature_group_min_size,
            )
        ] + added_miniatures
        if m_no_groups:
            group_computer = GroupComputer(
                group_min_size=self.settings.miniature_group_min_size,
                pixel_distance_radius=self.settings.miniature_pixel_distance_radius,
            )
            for dm in group_computer.batch_compute_groups(m_no_groups, database=self):
                m_dict[dm.miniature_identifier].set_group_signature(
                    self.settings.miniature_pixel_distance_radius,
                    self.settings.miniature_group_min_size,
                    len(dm.pixel_groups),
                )

        if have_removed or have_added:
            with open(self.__paths.miniatures_path.path, "w") as output_file:
                json.dump([m.to_dict() for m in available_miniatures], output_file)

        self.notifier.notify(notifications.NbMiniatures(len(available_miniatures)))

        if returns:
            miniatures = []
            for video in available_videos:
                miniature = m_dict[video["filename"].path]
                miniature.video_id = video["video_id"]
                miniatures.append(miniature)
            return miniatures

    @Profiler.profile_method()
    def compress_thumbnails(self):
        png_paths = []
        for entry in FileSystem.scandir(self.__paths.thumb_folder.path):
            path = AbsolutePath(entry.path)
            if (
                path.extension == THUMBNAIL_EXTENSION
                and not AbsolutePath.file_path(
                    path.get_directory(), path.title, JPEG_EXTENSION
                ).exists()
            ):
                png_paths.append(path.path)
        if not png_paths:
            self.notifier.notify(notifications.Message("no thumbnail to compress"))
            return
        notify_job_start(
            self.notifier, compress_thumbnails_to_jpeg, len(png_paths), "PNG thumbnails"
        )
        tasks = [(path, i, self.notifier) for i, path in enumerate(png_paths)]
        list(parallelize(compress_thumbnails_to_jpeg, tasks, ordered=False))

    def rename(self, new_name) -> None:
        self.__paths = self.__paths.renamed(new_name)
        self.notifier.set_log_path(self.__paths.log_path.path)
        self.set_path(self.__paths.json_path)

    def set_video_similarity(
        self, video_id: int, value: Optional[int], notify=True
    ) -> None:
        self.write_video_field(video_id, "similarity_id", value, notify=notify)

    def change_video_file_title(self, video_id: int, new_title: str) -> None:
        if functions.has_discarded_characters(new_title):
            raise exceptions.InvalidFileName(new_title)
        old_filename: AbsolutePath = self.read_video_field(video_id, "filename")
        if old_filename.file_title != new_title:
            self.change_video_path(video_id, old_filename.new_title(new_title))

    def delete_video(self, video_id: int) -> AbsolutePath:
        video_filename: AbsolutePath = self.read_video_field(video_id, "filename")
        video_filename.delete()
        self.delete_video_entry(video_id)
        return video_filename

    def refresh(self, ensure_miniatures=False) -> None:
        with Profiler(say("Reset thumbnail errors"), self.notifier):
            for video in self.select_videos_fields(
                ["video_id"], "readable", "found", "without_thumbnails"
            ):
                self.write_video_field(video["video_id"], "unreadable_thumbnail", False)
        self.update()
        self.ensure_thumbnails()
        if ensure_miniatures:
            self.ensure_miniatures()

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

    def delete_property_value(self, name: str, values: list) -> None:
        self.__del_prop_val(self.get_all_video_indices(), name, values)

    def move_property_value(self, old_name: str, values: list, new_name: str) -> None:
        modified = self.__del_prop_val(self.get_all_video_indices(), old_name, values)
        for video_id in modified:
            self.merge_prop_values(video_id, new_name, values)
        if modified:
            self._notify_properties_modified([old_name, new_name])

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
            old_values = set(self.get_prop_values(video_id, from_property))
            new_values = old_values - path_set
            if len(old_values) == len(new_values) + len(path_set):
                self.set_prop_values(video_id, from_property, new_values)
                self.merge_prop_values(video_id, to_property, [concat_path])
                modified.append(video_id)
        if modified:
            self._notify_properties_modified([from_property, to_property])
        return len(modified)

    def confirm_unique_moves(self) -> int:
        nb_moved = 0
        with self.to_save() as saver:
            for video_id in list(self.get_all_video_indices()):
                moves = self.read_video_field(video_id, "moves")
                if len(moves) == 1:
                    self.move_video_entry(video_id, moves[0]["video_id"])
                    nb_moved += 1
            saver.to_save = nb_moved
        return nb_moved

    def to_xspf_playlist(self, video_indices: Iterable[int]) -> AbsolutePath:
        tracks = "".join(
            f"<track><location>{self.get_video_filename(video_id).uri}</location></track>"
            for video_id in video_indices
        )
        file_content = (
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<playlist version="1" xmlns="http://xspf.org/ns/0/">'
            f"<trackList>{tracks}</trackList>"
            f"</playlist>"
        )
        temp_file_path = generate_temp_file_path("xspf")
        with open(temp_file_path, "w") as file:
            file.write(file_content)
        return AbsolutePath(temp_file_path)

    # Videos access and edition

    def open_containing_folder(self, video_id: int) -> str:
        return str(self.get_video_filename(video_id).locate_file())
