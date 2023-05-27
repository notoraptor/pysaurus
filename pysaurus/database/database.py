import logging
import multiprocessing
from collections import Counter
from typing import Any, Callable, Dict, Iterable, List, Optional, Set

import ujson as json

from pysaurus.application import exceptions
from pysaurus.core import functions, notifications
from pysaurus.core.components import AbsolutePath, Date, PathType
from pysaurus.core.constants import JPEG_EXTENSION, THUMBNAIL_EXTENSION
from pysaurus.core.file_utils import collect_file_titles, create_xspf_playlist
from pysaurus.core.job_notifications import notify_job_progress, notify_job_start
from pysaurus.core.modules import FileSystem, ImageUtils
from pysaurus.core.notifying import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.parallelization import parallelize, run_split_batch
from pysaurus.core.profiling import Profiler
from pysaurus.database import jobs_python
from pysaurus.database.jobs_python import compress_thumbnails_to_jpeg
from pysaurus.database.json_database import (
    DB_LOG_PATH,
    DB_MINIATURES_PATH,
    DB_THUMB_FOLDER,
    JsonDatabase,
)
from pysaurus.database.special_properties import SpecialProperties
from pysaurus.database.viewport.abstract_video_provider import AbstractVideoProvider
from pysaurus.database.viewport.video_filter import VideoFilter
from pysaurus.miniature.group_computer import GroupComputer
from pysaurus.miniature.miniature import Miniature
from pysaurus.video import Video
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

    def __init__(self, path, folders=None, notifier=None):
        # type: (PathType, Iterable[PathType], Notifier) -> None
        path = AbsolutePath.ensure(path)

        self._initial_pid = multiprocessing.current_process().pid
        logger.debug(f"Loaded database {path.title} in process {self._initial_pid}")
        assert self._initial_pid is not None

        # Load database
        super().__init__(path, folders, notifier or DEFAULT_NOTIFIER)
        # RAM data
        self.provider: Optional[AbstractVideoProvider] = VideoFilter(self)

        # Set special properties
        with Profiler(
            "install special properties", notifier=self.notifier
        ), self.to_save() as saver:
            saver.to_save = SpecialProperties.install(self)
        # Compress thumbnails if necessary.
        self.compress_thumbnails()

    def __getattribute__(self, item):
        attribute = super().__getattribute__(item)
        if callable(attribute):
            name = super().__getattribute__("name")
            prev_pid = super().__getattribute__("_initial_pid")
            curr_pid = multiprocessing.current_process().pid
            assert prev_pid == curr_pid, (
                f"Database {name}: method {item} called in different processes "
                f"(expected {prev_pid}, got {curr_pid})"
            )
        return attribute

    # Properties.

    name = property(lambda self: self.ways.db_folder.title)
    thumbnail_folder = property(lambda self: self.ways.get(DB_THUMB_FOLDER))

    @Profiler.profile_method()
    def update(self) -> None:
        current_date = Date.now()

        all_files = jobs_python.collect_video_paths(
            list(self.get_folders()), self.notifier
        )
        self._update_videos_not_found(all_files)
        files_to_update = self._find_video_paths_for_update(all_files)
        if not files_to_update:
            return

        backend_raptor = VideoRaptor()
        with Profiler(say("Collect videos info"), notifier=self.notifier):
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
                    extra_args=[self.ways.db_folder, self.notifier],
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
        thumb_folder = self.ways.get(DB_THUMB_FOLDER)
        db_folder = self.ways.db_folder

        # Get available thumbnails.
        with Profiler("Collect existing thumbnails", self.notifier):
            existing_thumb_names = collect_file_titles(thumb_folder, JPEG_EXTENSION)

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
                        self.write_video_fields(
                            video["video_id"], has_runtime_thumbnail=True
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
                    self.write_video_fields(
                        video["video_id"], has_runtime_thumbnail=True
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
            assert valid_thumb_names or not self.get_cached_videos()
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

        # Use Python video raptor to collect thumbnails.
        # Python video raptor can directly collect thumbnails into JPEG format,
        # without going through PNG->JPEG pipeline.
        backend_raptor = PythonVideoRaptor()
        with Profiler(title=say("Get thumbnails from JSON"), notifier=self.notifier):
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
                    extra_args=[db_folder, thumb_folder.best_path, self.notifier],
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
                    video_id, unreadable_thumbnail=True, has_runtime_thumbnail=False
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
        miniatures_path = self.ways.get(DB_MINIATURES_PATH)

        if miniatures_path.exists():
            with open(miniatures_path.assert_file().path) as miniatures_file:
                json_array = json.load(miniatures_file)
            if not isinstance(json_array, list):
                raise exceptions.InvalidMiniaturesJSON(miniatures_path)
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
            with open(miniatures_path.path, "w") as output_file:
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
        for entry in FileSystem.scandir(self.ways.get(DB_THUMB_FOLDER).path):
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

    def _clean_thumbnails(self, thumb_names: List[str]):
        notify_job_start(
            self.notifier, self._clean_thumbnails, len(thumb_names), "thumbnails"
        )
        for i, thumb_name in enumerate(thumb_names):
            for ext in (THUMBNAIL_EXTENSION, JPEG_EXTENSION):
                path = AbsolutePath.file_path(
                    self.ways.get(DB_THUMB_FOLDER), thumb_name, ext
                )
                if path.isfile():
                    path.delete()
                    assert not path.isfile()
            notify_job_progress(
                self.notifier, self._clean_thumbnails, None, i + 1, len(thumb_names)
            )

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

    def delete_video(self, video_id: int) -> AbsolutePath:
        video_filename: AbsolutePath = self.get_video_filename(video_id)
        video_filename.delete()
        self.delete_video_entry(video_id)
        return video_filename

    def reopen(self):
        self.notifier.set_log_path(self.ways.get(DB_LOG_PATH).path)

    def refresh(self, ensure_miniatures=False) -> None:
        with Profiler(say("Reset thumbnail errors"), self.notifier):
            for video in self.select_videos_fields(
                ["video_id"], "readable", "found", "without_thumbnails"
            ):
                self.write_video_fields(video["video_id"], unreadable_thumbnail=False)
        self.update()
        self.ensure_thumbnails()
        if ensure_miniatures:
            self.ensure_miniatures()

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

    def confirm_unique_moves(self) -> int:
        with self.to_save() as saver:
            unique_moves = list(self.moves_attribute.get_unique_moves())
            for video_id, moves in unique_moves:
                self.move_video_entry(video_id, moves[0]["video_id"])
            saver.to_save = len(unique_moves)
        return len(unique_moves)

    def to_xspf_playlist(self, video_indices: Iterable[int]) -> AbsolutePath:
        return create_xspf_playlist(map(self.get_video_filename, video_indices))

    def open_containing_folder(self, video_id: int) -> str:
        return str(self.get_video_filename(video_id).locate_file())

    def get_thumbnail(self, video_id):
        return AbsolutePath.file_path(
            self.ways.get(DB_THUMB_FOLDER),
            self.read_video_field(video_id, "thumb_name"),
            JPEG_EXTENSION,
        )
