import os
import sys
from multiprocessing import Pool
from typing import Dict, Iterable, List, Optional, Set

import ujson as json

from pysaurus.application import exceptions
from pysaurus.core import functions, job_notifications, notifications
from pysaurus.core.components import (
    AbsolutePath,
    DateModified,
    PathType,
)
from pysaurus.core.constants import CPU_COUNT, JPEG_EXTENSION, THUMBNAIL_EXTENSION
from pysaurus.core.job_utils import run_split_batch
from pysaurus.core.modules import FileSystem, ImageUtils
from pysaurus.core.notifier import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database import jobs_python
from pysaurus.database.db_paths import DbPaths
from pysaurus.database.jobs_python import job_image_to_jpeg
from pysaurus.database.json_database import JsonDatabase
from pysaurus.database.miniature_tools.group_computer import GroupComputer
from pysaurus.database.miniature_tools.miniature import Miniature
from pysaurus.database.special_properties import SpecialProperties
from pysaurus.database.video import Video
from pysaurus.database.video_runtime_info import VideoRuntimeInfo
from pysaurus.language.default_language import DefaultLanguage

try:
    from pysaurus.database.video_info import video_raptor as backend_raptor
except exceptions.CysaurusUnavailable:
    from pysaurus.database.video_info import backend_pyav as backend_raptor

    print("Using fallback backend for videos info and thumbnails.", file=sys.stderr)


class Database(JsonDatabase):
    __slots__ = ("__paths", "__message", "lang")

    def __init__(self, path, folders=None, notifier=None, lang=None):
        # type: (PathType, Iterable[PathType], Notifier, DefaultLanguage) -> None
        # Paths
        self.__paths = DbPaths(path)
        # RAM data
        self.__message = None
        self.lang = lang or DefaultLanguage
        # Set log file
        notifier = notifier or DEFAULT_NOTIFIER
        notifier.set_log_path(self.__paths.log_path.path)
        # Load database
        super().__init__(self.__paths.json_path, folders, notifier)
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
        # type: () -> Dict[str, DateModified]
        thumbs = {}
        with Profiler(self.lang.profile_collect_thumbnails, self.notifier):
            for entry in FileSystem.scandir(
                self.__paths.thumb_folder.path
            ):  # type: os.DirEntry
                if entry.path.lower().endswith(f".{JPEG_EXTENSION}"):
                    name = entry.name
                    thumbs[name[: -(len(JPEG_EXTENSION) + 1)]] = DateModified(
                        entry.stat().st_mtime
                    )
        return thumbs

    def __notify_missing_thumbnails(self):
        remaining_thumb_videos = [
            video.filename.path
            for video in self.get_videos("readable", "found", "without_thumbnails")
        ]
        self.notifier.notify(notifications.MissingThumbnails(remaining_thumb_videos))

    def __notify_filename_modified(self):
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

    # Public methods.

    @Profiler.profile_method()
    def update(self) -> None:
        current_date = DateModified.now()

        all_files = jobs_python.collect_video_paths(self.folders, self.notifier)
        self._update_videos_not_found(all_files)
        files_to_update = self._find_video_paths_for_update(all_files)
        if not files_to_update:
            return

        job_notifier = job_notifications.CollectVideoInfos(
            len(files_to_update), self.notifier
        )
        with Profiler(
            self.lang.profile_collect_video_infos.format(cpu_count=CPU_COUNT),
            notifier=self.notifier,
        ):
            results = run_split_batch(
                backend_raptor.backend_video_infos,
                files_to_update,
                CPU_COUNT,
                [self.__paths.db_folder, job_notifier],
            )

        videos = {}
        unreadable = []
        for arr in results:
            for d in arr:
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
                        video_state.properties.update(old_video.properties)
                        video_state.similarity_id = old_video.similarity_id
                        video_state.video_id = old_video.video_id
                    # Set special properties
                    SpecialProperties.set(video_state)
                videos[file_path] = video_state
                self.videos.pop(file_path, None)
                video_state.runtime = all_files[file_path]

        assert len(videos) == len(files_to_update)

        if videos:
            self.videos.update(videos)
            self.date = current_date
            self.save()
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

        with Profiler(self.lang.profile_check_video_thumbnails, notifier=self.notifier):
            for video in self.get_videos("readable"):
                thumb_name = video.thumb_name
                if not video.found:
                    video.runtime.has_thumbnail = thumb_name in existing_thumb_names
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
        with Profiler(
            self.lang.profile_check_unique_thumbnails, notifier=self.notifier
        ):
            for valid_thumb_name, vds in thumb_to_videos.items():
                if len(vds) == 1:
                    valid_thumb_names.add(valid_thumb_name)
                    vds[0].runtime.has_thumbnail = True
                else:
                    videos_without_thumbs.extend(vds)
        nb_videos_no_thumbs = len(videos_without_thumbs)
        del thumb_to_videos

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

        job_notifier = job_notifications.CollectVideoThumbnails(
            nb_videos_no_thumbs, self.notifier
        )
        with Profiler(
            title=self.lang.profile_collect_video_thumbnails.format(
                cpu_count=CPU_COUNT
            ),
            notifier=self.notifier,
        ):
            results = run_split_batch(
                backend_raptor.backend_video_thumbnails,
                [
                    (video.filename.path, video.thumb_name)
                    for video in videos_without_thumbs
                ],
                CPU_COUNT,
                [
                    self.__paths.db_folder,
                    self.__paths.thumb_folder.best_path,
                    job_notifier,
                ],
            )

        for arr in results:
            for d in arr:
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

        job_notifier = job_notifications.CollectVideoMiniatures(
            len(tasks), self.notifier
        )
        if tasks:
            have_added = True
            with Profiler(self.lang.profile_generate_miniatures, self.notifier):
                results = run_split_batch(
                    jobs_python.job_generate_miniatures,
                    tasks,
                    CPU_COUNT,
                    [job_notifier],
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
        job_notifier = job_notifications.CompressThumbnailsToJpeg(
            len(png_paths), self.notifier
        )
        tasks = [(path, i, job_notifier) for i, path in enumerate(png_paths)]
        with Profiler("compress thumbnails", self.notifier):
            with Pool(CPU_COUNT) as p:
                list(p.imap_unordered(job_image_to_jpeg, tasks))

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
        video.filename = path
        self.save()
        self.__notify_filename_modified()

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
        self.notifier.notify(notifications.VideoDeleted(video))
        self.notifier.notify(notifications.FieldsModified(["move_id", "quality"]))
        return video.filename

    def convert_prop_to_unique(self, name) -> None:
        if self.has_prop_type(name):
            prop_type = self.get_prop_type(name)
            if not prop_type.multiple:
                raise exceptions.PropertyAlreadyUnique(name)
            for video in self.query():
                if name in video.properties and len(video.properties[name]) > 1:
                    raise exceptions.PropertyToUniqueError(name, video)
            prop_type.multiple = False
            for video in self.query():
                if name in video.properties:
                    if video.properties[name]:
                        video.properties[name] = video.properties[name][0]
                    else:
                        del video.properties[name]
            self.save()

    def convert_prop_to_multiple(self, name) -> None:
        if self.has_prop_type(name):
            prop_type = self.get_prop_type(name)
            if prop_type.multiple:
                raise exceptions.PropertyAlreadyMultiple(name)
            prop_type.multiple = True
            for video in self.query():
                if name in video.properties:
                    video.properties[name] = [video.properties[name]]
            self.save()

    def set_video_properties(self, video_id: int, properties) -> Set[str]:
        video = self.__get_video_from_id(video_id)
        modified = video.update_properties(properties)
        self.save()
        self.notifier.notify(notifications.PropertiesModified(modified))
        return modified

    def refresh(self, ensure_miniatures=False) -> None:
        with Profiler(self.lang.profile_reset_thumbnail_errors):
            for video in self.get_videos("readable", "found", "without_thumbnails"):
                video.unreadable_thumbnail = False
        self.update()
        self.ensure_thumbnails()
        if ensure_miniatures:
            self.ensure_miniatures()

    def __del_prop_val(
        self, videos: Iterable[Video], name: str, values: list
    ) -> List[Video]:
        values = set(values)
        modified = []
        prop_type = self.get_prop_type(name)
        if prop_type.multiple:
            prop_type.validate(values)
            for video in videos:
                if name in video.properties and video.properties[name]:
                    new_values = set(video.properties[name])
                    len_before = len(new_values)
                    new_values = new_values - values
                    len_after = len(new_values)
                    if len_before > len_after:
                        video.properties[name] = sorted(new_values)
                        modified.append(video)
        else:
            for value in values:
                prop_type.validate(value)
            for video in videos:
                if name in video.properties and video.properties[name] in values:
                    del video.properties[name]
                    modified.append(video)
        if modified:
            self.save()
            self.notifier.notify(notifications.PropertiesModified([name]))
        return modified

    def delete_property_value(
        self, videos: Iterable[Video], name: str, values: list
    ) -> None:
        self.__del_prop_val(videos, name, values)

    def move_property_value(
        self, videos: Iterable[Video], old_name: str, values: list, new_name: str
    ) -> None:
        assert len(values) == 1, values
        value = values[0]
        prop_type = self.get_prop_type(new_name)
        prop_type.validate([value] if prop_type.multiple else value)
        videos = self.__del_prop_val(videos, old_name, [value])
        if prop_type.multiple:
            for video in videos:
                new_values = set(video.properties.get(new_name, ()))
                new_values.add(value)
                video.properties[new_name] = sorted(new_values)
        else:
            for video in videos:
                video.properties[new_name] = value
        if videos:
            self.save()
            self.notifier.notify(notifications.PropertiesModified([old_name, new_name]))

    def edit_property_value(
        self, videos: Iterable[Video], name: str, old_values: list, new_value: object
    ) -> bool:
        old_values = set(old_values)
        modified = False
        prop_type = self.get_prop_type(name)
        if prop_type.multiple:
            prop_type.validate(old_values)
            prop_type.validate([new_value])
            for video in videos:
                if name in video.properties and video.properties[name]:
                    new_values = set(video.properties[name])
                    len_before = len(new_values)
                    new_values = new_values - old_values
                    len_after = len(new_values)
                    if len_before > len_after:
                        new_values.add(new_value)
                        video.properties[name] = sorted(new_values)
                        modified = True
        else:
            for old_value in old_values:
                prop_type.validate(old_value)
            prop_type.validate(new_value)
            for video in videos:
                if name in video.properties and video.properties[name] in old_values:
                    video.properties[name] = new_value
                    modified = True
        if modified:
            self.save()
            self.notifier.notify(notifications.PropertiesModified([name]))
        return modified

    def edit_property_for_videos(
        self,
        name: str,
        video_indices: List[int],
        values_to_add: list,
        values_to_remove: list,
    ) -> None:
        print("TO CHANGE", len(video_indices), video_indices)
        prop_type = self.get_prop_type(name)
        if prop_type.multiple:
            values_to_add = prop_type(values_to_add)
            values_to_remove = prop_type(values_to_remove)
        else:
            assert len(values_to_add) < 2
            values_to_add = [prop_type(value) for value in values_to_add]
            values_to_remove = {prop_type(value) for value in values_to_remove}
        video_indices = set(video_indices)
        for video_id in video_indices:
            video = self.__get_video_from_id(video_id)
            if prop_type.multiple:
                values = set(video.properties.get(prop_type.name, ()))
                values.difference_update(values_to_remove)
                values.update(values_to_add)
                if values:
                    video.properties[prop_type.name] = sorted(values)
                elif prop_type.name in video.properties:
                    del video.properties[prop_type.name]
            else:
                if (
                    values_to_remove
                    and prop_type.name in video.properties
                    and video.properties[prop_type.name] in values_to_remove
                ):
                    del video.properties[prop_type.name]
                if values_to_add:
                    video.properties[prop_type.name] = values_to_add[0]
        self.save()
        self.notifier.notify(notifications.PropertiesModified([name]))

    def count_property_values(
        self, name: str, video_indices: List[int]
    ) -> Dict[object, int]:
        prop_type = self.get_prop_type(name)
        value_to_count = {}
        video_indices = set(video_indices)
        for video_id in video_indices:
            video = self.__get_video_from_id(video_id)
            if prop_type.multiple:
                values = video.properties.get(prop_type.name, [])
            elif prop_type.name in video.properties:
                values = [video.properties[prop_type.name]]
            else:
                values = []
            for value in values:
                value_to_count[value] = value_to_count.get(value, 0) + 1
        return value_to_count

    def fill_property_with_terms(
        self, videos: Iterable[Video], prop_name: str, only_empty=False
    ) -> None:
        prop_type = self.get_prop_type(prop_name)
        assert prop_type.multiple
        assert prop_type.type is str
        for video in videos:
            if only_empty and video.properties.get(prop_name, None):
                continue
            values = video.terms(as_set=True)
            values.update(video.properties.get(prop_name, ()))
            video.properties[prop_name] = prop_type(values)
        self.save()
        self.notifier.notify(notifications.PropertiesModified([prop_name]))

    def prop_to_lowercase(self, prop_name):
        prop_type = self.get_prop_type(prop_name)
        assert prop_type.type is str
        for video in self.query():
            if prop_name in video.properties:
                if prop_type.multiple:
                    video.properties[prop_name] = sorted(
                        set(
                            value.strip().lower()
                            for value in video.properties[prop_name]
                        )
                    )
                else:
                    video.properties[prop_name] = (
                        video.properties[prop_name].strip().lower()
                    )
        self.save()
        self.notifier.notify(notifications.PropertiesModified([prop_name]))

    def prop_to_uppercase(self, prop_name):
        prop_type = self.get_prop_type(prop_name)
        assert prop_type.type is str
        for video in self.query():
            if prop_name in video.properties:
                if prop_type.multiple:
                    video.properties[prop_name] = sorted(
                        set(
                            value.strip().upper()
                            for value in video.properties[prop_name]
                        )
                    )
                else:
                    video.properties[prop_name] = (
                        video.properties[prop_name].strip().upper()
                    )
        self.save()
        self.notifier.notify(notifications.PropertiesModified([prop_name]))

    def move_concatenated_prop_val(
        self, videos: Iterable[Video], path: list, from_property: str, to_property: str
    ) -> int:
        from_prop_type = self.get_prop_type(from_property)
        to_prop_type = self.get_prop_type(to_property)
        assert from_prop_type.multiple
        assert to_prop_type.type is str
        from_prop_type.validate(path)
        new_value = " ".join(str(value) for value in path)
        to_prop_type.validate([new_value] if to_prop_type.multiple else new_value)

        modified = []
        path_set = set(path)
        for video in videos:
            if from_property in video.properties and video.properties[from_property]:
                new_values = set(video.properties[from_property])
                len_before = len(new_values)
                new_values = new_values - path_set
                if len_before == len(new_values) + len(path):
                    video.properties[from_property] = sorted(new_values)
                    modified.append(video)

        if to_prop_type.multiple:
            for video in modified:
                new_values = set(video.properties.get(to_property, ()))
                new_values.add(new_value)
                video.properties[to_property] = sorted(new_values)
        else:
            for video in modified:
                video.properties[to_property] = new_value

        if modified:
            self.save()
            self.notifier.notify(
                notifications.PropertiesModified([from_property, to_property])
            )

        return len(modified)

    def move_video_entry(self, from_id, to_id, save=True):
        from_video = self.__get_video_from_id(from_id)
        to_video = self.__get_video_from_id(to_id)
        assert not from_video.found
        assert to_video.found
        transferred_properties = {}
        for prop_name, prop_val in from_video.properties.items():
            prop_type = self.get_prop_type(prop_name)
            if prop_type.multiple:
                transferred_properties[prop_name] = prop_type(
                    prop_val + to_video.properties.get(prop_name, [])
                )
            else:
                transferred_properties[prop_name] = prop_val
        to_video.properties.update(transferred_properties)
        to_video.similarity_id = from_video.similarity_id
        self.delete_video(from_id, save=save)

    def confirm_unique_moves(self):
        nb_moved = 0
        for video in self.get_videos("readable", "not_found"):
            moves = video.moves
            if len(moves) == 1:
                self.move_video_entry(video.video_id, moves[0]["video_id"], False)
                nb_moved += 1
        if nb_moved:
            self.save()
        return nb_moved

    def set_message(self, message: str):
        self.__message = message

    def flush_message(self):
        message = self.__message
        self.__message = None
        return message

    def get_predictor(self, prop_name):
        return self.predictors.get(prop_name, None)

    def set_predictor(self, prop_name: str, theta: List[float]):
        self.predictors[prop_name] = theta

    # Videos access and edition

    def __get_video_from_id(self, video_id: int) -> Video:
        video = self.id_to_video[video_id]
        assert video.readable
        return video

    def get_video_filename(self, video_id: int) -> AbsolutePath:
        return self.id_to_video[video_id].filename

    def get_videos_field(self, indices: Iterable[int], field: str) -> Iterable:
        return (getattr(self.id_to_video[video_id], field) for video_id in indices)

    def set_videos_field_with_same_value(
        self, indices: Iterable[int], field: str, value
    ) -> None:
        for video_id in indices:
            setattr(self.id_to_video[video_id], field, value)

    def set_videos_field(self, indices: Iterable[int], field, values: Iterable) -> None:
        for video_id, value in zip(indices, values):
            setattr(self.id_to_video[video_id], field, value)
