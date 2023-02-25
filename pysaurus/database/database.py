import os
import sys
from collections import Counter
from typing import Dict, Iterable, List, Optional, Set, Tuple

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
from pysaurus.core.functions import generate_infinite, generate_temp_file_path
from pysaurus.core.job_notifications import notify_job_progress, notify_job_start
from pysaurus.core.modules import FileSystem, ImageUtils
from pysaurus.core.notifying import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.parallelization import parallelize, run_split_batch
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database import jobs_python
from pysaurus.database.db_paths import DbPaths
from pysaurus.database.jobs_python import compress_thumbnails_to_jpeg
from pysaurus.database.json_database import JsonDatabase
from pysaurus.database.special_properties import SpecialProperties
from pysaurus.database.viewport.abstract_video_provider import AbstractVideoProvider
from pysaurus.database.viewport.video_filter import VideoSelector
from pysaurus.miniature.group_computer import GroupComputer
from pysaurus.miniature.miniature import Miniature
from pysaurus.video.video import Video
from pysaurus.video.video_indexer import VideoIndexer
from pysaurus.video.video_runtime_info import VideoRuntimeInfo
from saurus.language import say

try:
    from pysaurus.video_raptor.video_raptor_native import VideoRaptor
except exceptions.CysaurusUnavailable:
    from pysaurus.video_raptor.video_raptor_pyav import VideoRaptor

    print("Using fallback backend for videos info and thumbnails.", file=sys.stderr)


class Database(JsonDatabase):
    __slots__ = ("__paths", "lang", "provider")

    def __init__(self, path, folders=None, notifier=None, lang=None):
        # type: (PathType, Iterable[PathType], Notifier, DefaultLanguage) -> None
        # Paths
        self.__paths = DbPaths(path)
        # RAM data
        self.lang = lang or DefaultLanguage
        self.provider: Optional[AbstractVideoProvider] = VideoSelector(self)
        # Set log file
        notifier = notifier or DEFAULT_NOTIFIER
        notifier.set_log_path(self.__paths.log_path.path)
        # Load database
        super().__init__(
            self.__paths.json_path,
            folders,
            notifier,
            # indexer=SqlVideoIndexer(self.__paths.index_path.path),
            indexer=VideoIndexer(),
        )
        # Set special properties
        with Profiler("install special properties", notifier=self.notifier):
            SpecialProperties.install(self)
        self.compress_thumbnails()

    # Properties.

    name = property(lambda self: self.__paths.db_folder.title)
    thumbnail_folder = property(lambda self: self.__paths.thumb_folder)
    video_folders = property(lambda self: list(self.folders))

    # Private methods.

    def _update_videos_not_found(
        self, file_paths: Dict[AbsolutePath, VideoRuntimeInfo]
    ):
        for video_state in self.videos.values():
            video_state.runtime.is_file = video_state.filename in file_paths

    def _find_video_paths_for_update(
        self, file_paths: Dict[AbsolutePath, VideoRuntimeInfo]
    ) -> List[str]:
        all_file_names = []
        for file_name, file_info in file_paths.items():
            video: Video = self.videos.get(file_name, None)
            if (
                video is None
                or file_info.mtime != video.runtime.mtime
                or file_info.size != video.file_size
                or file_info.driver_id != video.runtime.driver_id
                or (video.readable and not SpecialProperties.all_in(video))
            ):
                all_file_names.append(file_name.path)
        all_file_names.sort()
        return all_file_names

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

    def __notify_missing_thumbnails(self):
        remaining_thumb_videos = [
            video.filename.path
            for video in self.get_videos("readable", "found", "without_thumbnails")
        ]
        self.notifier.notify(notifications.MissingThumbnails(remaining_thumb_videos))

    def __notify_filename_modified(self, video: Video, old_path: AbsolutePath):
        self.notifier.notify(
            notifications.FieldsModified(
                (
                    "title",
                    "title_numeric",
                    "file_title",
                    "file_title_numeric",
                    "filename_numeric",
                    "disk",
                    "filename",
                )
            )
        )
        self._update_video_path_in_index(video, old_path)

    def _notify_properties_modified(
        self, properties: Iterable[str], videos: Iterable[Video]
    ):
        self._update_videos_in_index(videos)
        self.notifier.notify(notifications.PropertiesModified(properties))

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

        all_files = jobs_python.collect_video_paths(self.folders, self.notifier)
        self._update_videos_not_found(all_files)
        files_to_update = self._find_video_paths_for_update(all_files)
        if not files_to_update:
            return

        backend_raptor = VideoRaptor()
        notify_job_start(
            self.notifier,
            backend_raptor.collect_video_info,
            len(files_to_update),
            "videos",
        )
        with Profiler(
            say("Collect videos info"),
            notifier=self.notifier,
        ):
            results = run_split_batch(
                backend_raptor.collect_video_info,
                files_to_update,
                extra_args=[self.__paths.db_folder, self.notifier],
            )

        videos = {}
        unreadable = []
        replaced = []
        for arr in results:
            for d in arr:
                d = Video.ensure_short_keys(d, backend_raptor.RETURNS_SHORT_KEYS)
                file_path = AbsolutePath.ensure(d["f"])
                if len(d) == 2:
                    video_state = Video(
                        filename=file_path.path,
                        file_size=file_path.get_size(),
                        errors=set(d["e"]),
                        unreadable=True,
                        database=self,
                    )
                    unreadable.append(video_state)
                else:
                    video_state = Video.from_dict(d, database=self)
                    # Get previous properties, if available
                    if file_path in self.videos and self.videos[file_path].readable:
                        old_video = self.videos[file_path]
                        video_state.set_properties(old_video.properties)
                        video_state.similarity_id = old_video.similarity_id
                        video_state.video_id = old_video.video_id
                    # Set special properties
                    SpecialProperties.set(video_state)
                videos[file_path] = video_state
                if file_path in self.videos:
                    replaced.append(self.videos.pop(file_path))
                video_state.runtime = all_files[file_path]

        assert len(videos) == len(files_to_update)

        if videos:
            self.videos.update(videos)
            self.date = current_date
            self.save()
            self._update_videos_in_index(videos.values())
        if unreadable:
            self.notifier.notify(
                notifications.VideoInfoErrors(
                    {
                        video_state.filename: video_state.errors
                        for video_state in unreadable
                    }
                )
            )

    @Profiler.profile_method()
    def ensure_thumbnails(self) -> None:
        valid_thumb_names = set()
        videos_without_thumbs = []
        thumb_to_videos: Dict[str, List[Video]] = {}
        thumb_errors = {}

        # Collect videos with and without thumbnails.
        existing_thumb_names = self.__check_thumbnails_on_disk()

        with Profiler(say("Check videos thumbnails"), notifier=self.notifier):
            for video in self.get_videos("readable"):
                thumb_name = video.thumb_name
                if not video.found:
                    if thumb_name in existing_thumb_names:
                        video.runtime.has_thumbnail = True
                        valid_thumb_names.add(thumb_name)
                elif not video.unreadable_thumbnail:
                    if (
                        thumb_name in existing_thumb_names
                        and existing_thumb_names[thumb_name] > video.date
                    ):
                        thumb_to_videos.setdefault(thumb_name, []).append(video)
                    else:
                        videos_without_thumbs.append(video)

        # If a thumbnail name is associated to many videos,
        # consider these videos don't have thumbnails.
        with Profiler(say("Check unique thumbnails"), notifier=self.notifier):
            for valid_thumb_name, vds in thumb_to_videos.items():
                if len(vds) == 1:
                    valid_thumb_names.add(valid_thumb_name)
                    vds[0].runtime.has_thumbnail = True
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
            self._clean_thumbnails(thumbs_to_clean)

        if not videos_without_thumbs:
            self.save()
            self.__notify_missing_thumbnails()
            return

        for video in videos_without_thumbs:
            base_thumb_name = video.thumb_name
            thumb_name_index = 0
            thumb_name = base_thumb_name
            while thumb_name in valid_thumb_names:
                thumb_name = f"{base_thumb_name}_{thumb_name_index}"
                thumb_name_index += 1
            video.thumb_name = thumb_name
            video.runtime.has_thumbnail = True
            valid_thumb_names.add(thumb_name)
        del valid_thumb_names
        self.save()

        backend_raptor = VideoRaptor()
        notify_job_start(
            self.notifier,
            backend_raptor.collect_video_thumbnails,
            nb_videos_no_thumbs,
            "videos",
        )
        with Profiler(
            title=say(
                "Get thumbnails from JSON",
            ),
            notifier=self.notifier,
        ):
            results = run_split_batch(
                backend_raptor.collect_video_thumbnails,
                [
                    (video.filename.path, video.thumb_name)
                    for video in videos_without_thumbs
                ],
                extra_args=[
                    self.__paths.db_folder,
                    self.__paths.thumb_folder.best_path,
                    self.notifier,
                ],
            )

        for arr in results:
            for d in arr:
                d = Video.ensure_short_keys(d, backend_raptor.RETURNS_SHORT_KEYS)
                assert len(d) == 2 and "f" in d and "e" in d
                file_name = d["f"]
                file_path = AbsolutePath.ensure(file_name)
                thumb_errors[file_name] = d["e"]
                video = self.videos[file_path]
                video.unreadable_thumbnail = True
                video.runtime.has_thumbnail = False

        if thumb_errors:
            self.notifier.notify(notifications.VideoThumbnailErrors(thumb_errors))

        self.compress_thumbnails()
        self.save()
        self.__notify_missing_thumbnails()

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
                if identifier in self.videos and ImageUtils.DEFAULT_THUMBNAIL_SIZE == (
                    dct["w"],
                    dct["h"],
                ):
                    identifiers.add(identifier)
                    valid_dictionaries.append(dct)
            have_removed = len(valid_dictionaries) != len(json_array)
            del json_array

        available_videos = self.get_videos("readable", "with_thumbnails")
        tasks = [
            (video.filename, video.thumbnail_path)
            for video in available_videos
            if video.filename not in identifiers
        ]

        if tasks:
            notify_job_start(
                self.notifier,
                jobs_python.generate_video_miniatures,
                len(tasks),
                "videos",
            )
            have_added = True
            with Profiler(say("Generating miniatures."), self.notifier):
                results = run_split_batch(
                    jobs_python.generate_video_miniatures,
                    tasks,
                    extra_args=[self.notifier],
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
                miniature = m_dict[video.filename.path]
                miniature.video_id = video.video_id
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

    def set_folders(self, folders) -> None:
        folders = sorted(AbsolutePath.ensure(folder) for folder in folders)
        if folders == sorted(self.folders):
            return
        folders_tree = PathTree(folders)
        for video in self.videos.values():
            video.discarded = not folders_tree.in_folders(video.filename)
        self.folders = set(folders)
        self.save()

    def set_similarity(self, video_id: int, value: Optional[int]):
        video = self.__get_video_from_id(video_id)
        video.similarity_id = value
        self.save()
        self.notifier.notify(notifications.FieldsModified(["similarity_id"]))

    def change_video_file_title(self, video_id: int, new_title: str) -> None:
        if functions.has_discarded_characters(new_title):
            raise exceptions.InvalidFileName(new_title)
        video = self.__get_video_from_id(video_id)
        if video.filename.file_title != new_title:
            self.change_video_path(video_id, video.filename.new_title(new_title))

    def change_video_path(self, video_id: int, path: AbsolutePath) -> AbsolutePath:
        path = AbsolutePath.ensure(path)
        assert path.isfile()
        video = self.__get_video_from_id(video_id)
        assert video.filename != path
        old_filename = video.filename

        del self.videos[video.filename]
        self.videos[path] = video
        # TODO video.filename should be immutable
        # We should instead copy video object with a new filename
        video.filename = path
        self.save()
        self.__notify_filename_modified(video, old_filename)

        return old_filename

    def delete_video(self, video_id: int, save=True) -> AbsolutePath:
        video = self.id_to_video[video_id]
        video.filename.delete()
        self.videos.pop(video.filename, None)
        self.id_to_video.pop(video.video_id, None)
        if video.readable:
            video.thumbnail_path.delete()
        if save:
            self.save()
        self._remove_video_from_index(video)
        self.notifier.notify(notifications.VideoDeleted(video))
        self.notifier.notify(notifications.FieldsModified(["move_id", "quality"]))
        return video.filename

    def set_video_properties(self, video_id: int, properties: dict) -> Set[str]:
        video = self.__get_video_from_id(video_id)
        modified = video.set_validated_properties(properties)
        self.save()
        self._notify_properties_modified(modified, [video])
        return modified

    def refresh(self, ensure_miniatures=False) -> None:
        with Profiler(say("Reset thumbnail errors"), self.notifier):
            for video in self.get_videos("readable", "found", "without_thumbnails"):
                video.unreadable_thumbnail = False
        self.update()
        self.ensure_thumbnails()
        if ensure_miniatures:
            self.ensure_miniatures()

    def __del_prop_val(
        self, videos: Iterable[Video], name: str, values: list
    ) -> List[Video]:
        modified = []
        values = set(self.validate_prop_values(name, values))
        for video in videos:
            previous_values = set(self.get_prop_values(video, name))
            new_values = previous_values - values
            if len(previous_values) > len(new_values):
                self.set_prop_values(video, name, new_values)
                modified.append(video)
        if modified:
            self.save()
            self._notify_properties_modified([name], modified)
        return modified

    def delete_property_value(self, name: str, values: list) -> None:
        self.__del_prop_val(self.videos.values(), name, values)

    def move_property_value(self, old_name: str, values: list, new_name: str) -> None:
        modified = self.__del_prop_val(self.videos.values(), old_name, values)
        for video in modified:
            self.merge_prop_values(video, new_name, values)
        if modified:
            self.save()
            self._notify_properties_modified([old_name, new_name], modified)

    def edit_property_value(
        self, name: str, old_values: list, new_value: object
    ) -> bool:
        modified = []
        old_values = set(self.validate_prop_values(name, old_values))
        (new_value,) = self.validate_prop_values(name, [new_value])
        for video in self.videos.values():
            previous_values = set(self.get_prop_values(video, name))
            next_values = previous_values - old_values
            if len(previous_values) > len(next_values):
                next_values.add(new_value)
                self.set_prop_values(video, name, next_values)
                modified.append(video)
        if modified:
            self.save()
            self._notify_properties_modified([name], modified)
        return bool(modified)

    def edit_property_for_videos(
        self,
        videos: List[Video],
        name: str,
        values_to_add: list,
        values_to_remove: list,
    ) -> None:
        print(
            "Edit",
            len(videos),
            "video props, add",
            values_to_add,
            "remove",
            values_to_remove,
        )
        values_to_add = self.validate_prop_values(name, values_to_add)
        values_to_remove = set(self.validate_prop_values(name, values_to_remove))
        modified = []
        for video in videos:
            values = set(self.get_prop_values(video, name)) - values_to_remove
            self.set_prop_values(video, name, values)
            self.merge_prop_values(video, name, values_to_add)
            modified.append(video)
        self.save()
        self._notify_properties_modified([name], modified)

    def count_property_values(
        self, videos: List[Video], name: str
    ) -> List[Tuple[object, int]]:
        count = Counter()
        for video in videos:
            count.update(self.get_prop_values(video, name))
        return sorted(count.items())

    def fill_property_with_terms(self, prop_name: str, only_empty=False) -> None:
        assert self.has_prop_type(prop_name, with_type=str, multiple=True)
        modified = []
        for video in self.videos.values():
            values = set(self.get_prop_values(video, prop_name))
            if only_empty and values:
                continue
            self.set_prop_values(video, prop_name, values | video.terms(as_set=True))
            modified.append(video)
        if modified:
            self.save()
            self._notify_properties_modified([prop_name], modified)

    def prop_to_lowercase(self, prop_name):
        assert self.has_prop_type(prop_name, with_type=str)
        modified = []
        for video in self.query():
            values = self.get_prop_values(video, prop_name)
            new_values = [value.strip().lower() for value in values]
            if values and new_values != values:
                self.set_prop_values(video, prop_name, new_values)
                modified.append(video)
        if modified:
            self.save()
            self._notify_properties_modified([prop_name], modified)

    def prop_to_uppercase(self, prop_name):
        assert self.has_prop_type(prop_name, with_type=str)
        modified = []
        for video in self.query():
            values = self.get_prop_values(video, prop_name)
            new_values = [value.strip().upper() for value in values]
            if values and new_values != values:
                self.set_prop_values(video, prop_name, new_values)
                modified.append(video)
        if modified:
            self.save()
            self._notify_properties_modified([prop_name], modified)

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
        for video in self.videos.values():
            old_values = set(self.get_prop_values(video, from_property))
            new_values = old_values - path_set
            if len(old_values) == len(new_values) + len(path_set):
                self.set_prop_values(video, from_property, new_values)
                self.merge_prop_values(video, to_property, [concat_path])
                modified.append(video)
        if modified:
            self.save()
            self._notify_properties_modified([from_property, to_property], modified)
        return len(modified)

    def move_video_entry(self, from_id, to_id, save=True):
        from_video = self.__get_video_from_id(from_id)
        to_video = self.__get_video_from_id(to_id)
        assert not from_video.found
        assert to_video.found
        for prop_name in self.get_prop_names():
            self.merge_prop_values(
                to_video, prop_name, self.get_prop_values(from_video, prop_name)
            )
        to_video.similarity_id = from_video.similarity_id
        self.delete_video(from_id, save=save)

    def confirm_unique_moves(self) -> int:
        nb_moved = 0
        for video in self.get_videos("readable", "not_found"):
            moves = video.moves
            if len(moves) == 1:
                self.move_video_entry(video.video_id, moves[0]["video_id"], False)
                nb_moved += 1
        if nb_moved:
            self.save()
        return nb_moved

    def get_predictor(self, prop_name):
        return self.predictors.get(prop_name, None)

    def set_predictor(self, prop_name: str, theta: List[float]):
        self.predictors[prop_name] = theta

    @classmethod
    def to_xspf_playlist(cls, videos: Iterable[Video]) -> AbsolutePath:
        tracks = "".join(
            f"<track><location>{video.filename.uri}</location></track>"
            for video in videos
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

    def __get_video_from_id(self, video_id: int) -> Video:
        video = self.id_to_video[video_id]
        assert video.readable
        return video

    def get_video_filename(self, video_id: int) -> AbsolutePath:
        return self.id_to_video[video_id].filename

    def open_video(self, video_id: int):
        self.id_to_video[video_id].filename.open()

    def open_containing_folder(self, video_id: int) -> str:
        return str(self.id_to_video[video_id].filename.locate_file())

    def get_videos_field(self, indices: Iterable[int], field: str) -> Iterable:
        return (getattr(self.id_to_video[video_id], field) for video_id in indices)

    def set_similarity_id(self, video_indices: Iterable[int], **kwargs) -> None:
        """Set similarity ID for given videos

        :param video_indices: iterable of video indices to set
        :param kwargs: one of following:
            - values: similarity indices to set. Should be as long as video_indices.
            - value: similarity ID to set for all video indices.
        """
        assert len(kwargs) == 1
        if "values" in kwargs:
            values: Iterable = kwargs["values"]
        else:
            assert "value" in kwargs
            values: Iterable = generate_infinite(kwargs["value"])
        for video_id, value in zip(video_indices, values):
            self.id_to_video[video_id].similarity_id = value
