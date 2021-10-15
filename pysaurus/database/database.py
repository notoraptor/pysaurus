import os
import sys
from collections import namedtuple
from multiprocessing import Pool
from typing import Dict, Iterable, List, Optional, Sequence, Set, Union

import ujson as json

from pysaurus.application import exceptions
from pysaurus.core import functions, job_notifications, notifications
from pysaurus.core.components import (
    AbsolutePath,
    DateModified,
    PathType,
)
from pysaurus.core.constants import CPU_COUNT, THUMBNAIL_EXTENSION
from pysaurus.core.modules import FileSystem, ImageUtils
from pysaurus.core.notifier import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database import jobs_python
from pysaurus.database.db_cache import DbCache
from pysaurus.database.db_settings import DbSettings
from pysaurus.database.db_utils import new_sub_file, new_sub_folder
from pysaurus.database.db_video_attribute import (
    PotentialMoveAttribute,
    QualityAttribute,
)
from pysaurus.database.miniature_tools.group_computer import GroupComputer
from pysaurus.database.miniature_tools.miniature import Miniature
from pysaurus.database.properties import PropType
from pysaurus.database.special_properties import SpecialProperties
from pysaurus.database.video import Video
from pysaurus.database.video_runtime_info import VideoRuntimeInfo
from pysaurus.database.video_state import VideoState

try:
    from pysaurus.database.video_info import video_raptor as backend_raptor
except exceptions.CysaurusUnavailable:
    from pysaurus.database.video_info import backend_pyav as backend_raptor

    print("Using fallback backend for videos info and thumbnails.", file=sys.stderr)


class Database:
    __slots__ = (
        "__db_folder",
        "__thumb_folder",
        "__json_path",
        "__tmp_json_path_next",
        "__tmp_json_path_prev",
        "__miniatures_path",
        "__log_path",
        "__settings",
        "__date",
        "__folders",
        "__videos",
        "__prop_types",
        "__notifier",
        "__id_to_video",
        "__cache",
        "quality_attribute",
        "moves_attribute",
        "__prop_parser",
        "__save_id",
        "__message",
        "__predictors",
    )

    def __init__(self, path, folders=None, clear_old_folders=False, notifier=None):
        # type: (PathType, Iterable[PathType], bool, Notifier) -> None
        # Paths
        self.__db_folder = AbsolutePath.ensure_directory(path)
        self.__thumb_folder = new_sub_folder(self.__db_folder, "thumbnails").mkdir()
        self.__json_path = new_sub_file(self.__db_folder, "json")
        self.__tmp_json_path_prev = new_sub_file(self.__db_folder, "prev.json")
        self.__tmp_json_path_next = new_sub_file(self.__db_folder, "next.json")
        self.__miniatures_path = new_sub_file(self.__db_folder, "miniatures.json")
        self.__log_path = new_sub_file(self.__db_folder, "log")
        # Database data
        self.__settings = DbSettings()
        self.__date = DateModified.now()
        self.__folders = set()  # type: Set[AbsolutePath]
        self.__videos = {}  # type: Dict[AbsolutePath, Union[VideoState, Video]]
        self.__prop_types = {}  # type: Dict[str, PropType]
        self.__predictors = {}  # type: Dict[str, List[float]]
        # RAM data
        self.__cache = DbCache(self)
        self.__notifier = notifier or DEFAULT_NOTIFIER
        self.__id_to_video = {}  # type: Dict[int, Union[VideoState, Video]]
        self.__prop_parser = {}  # type: Dict[str, callable]
        self.__save_id = 0
        self.__message = None
        self.quality_attribute = QualityAttribute(self)
        self.moves_attribute = PotentialMoveAttribute(self)
        # Set log file
        self.__notifier.set_log_path(self.__log_path.path)
        # Load database
        self.__load(folders, clear_old_folders)
        # Set special properties
        SpecialProperties.install(self)

    # Properties.

    nb_entries = property(lambda self: len(self.__videos))
    nb_discarded = property(lambda self: len(self.get_videos("discarded")))
    folder = property(lambda self: self.__db_folder)
    video_folders = property(lambda self: list(self.__folders))
    thumbnail_folder = property(lambda self: self.__thumb_folder)
    notifier = property(lambda self: self.__notifier)
    iteration = property(lambda self: self.__save_id)

    # Private methods.

    @Profiler.profile_method()
    def __load(self, folders=None, clear_old_folders=False):
        # type: (Optional[Iterable[PathType]], Optional[bool]) -> None

        if self.__json_path.exists():
            with open(self.__json_path.assert_file().path) as output_file:
                json_dict = json.load(output_file)
            if not isinstance(json_dict, dict):
                raise exceptions.InvalidDatabaseJSON(self.__json_path)
        else:
            json_dict = {}

        # Parsing settings.
        self.__settings.update(json_dict.get("settings", {}))

        # Parsing date.
        if "date" in json_dict:
            self.__date = DateModified(json_dict["date"])

        # Parsing folders.
        if not clear_old_folders:
            self.__folders.update(
                AbsolutePath(path) for path in json_dict.get("folders", ())
            )
        if folders:
            self.__folders.update(AbsolutePath.ensure(path) for path in folders)

        # Parsing video property types.
        for prop_dict in json_dict.get("prop_types", ()):
            self.add_prop_type(PropType.from_dict(prop_dict), save=False)

        # Parsing predictors
        self.__predictors = json_dict.get("predictors", {})

        # Parsing videos.
        folders_tree = PathTree(self.__folders)
        for video_dict in json_dict.get("videos", ()):
            if video_dict["U"]:
                video_state = VideoState.from_dict(video_dict, self)
            else:
                video_state = Video.from_dict(video_dict, self)
            if not folders_tree.in_folders(video_state.filename):
                video_state.discarded = True
            self.__videos[video_state.filename] = video_state

        self.save(on_new_identifiers=True)
        self.__notifier.notify(notifications.DatabaseLoaded(self))

    @Profiler.profile_method()
    def save(self, on_new_identifiers=False):
        """Save database on disk.

        :param on_new_identifiers: if True, save only if new video IDs were generated.
        """
        if not self.__ensure_identifiers() and on_new_identifiers:
            return
        self.__save_id += 1
        # Save database.
        json_output = {
            "settings": self.__settings.to_dict(),
            "date": self.__date.time,
            "folders": sorted(folder.path for folder in self.__folders),
            "prop_types": [prop.to_dict() for prop in self.__prop_types.values()],
            "predictors": self.__predictors,
            "videos": sorted(
                (video.to_dict() for video in self.__videos.values()),
                key=lambda dct: dct["f"],
            ),
        }

        # functions.assert_data_is_serializable(json_output)
        with open(self.__tmp_json_path_next.path, "w") as output_file:
            json.dump(json_output, output_file)
        self.__tmp_json_path_prev.delete()
        FileSystem.rename(self.__json_path.path, self.__tmp_json_path_prev.path)
        FileSystem.rename(self.__tmp_json_path_next.path, self.__json_path.path)
        assert not self.__tmp_json_path_next.exists()
        assert self.__tmp_json_path_prev.isfile()
        assert self.__json_path.isfile()

        self.__notifier.notify(notifications.DatabaseSaved(self))

    @staticmethod
    def __transfer_db_path(
        path: AbsolutePath, old_folder: AbsolutePath, new_folder: AbsolutePath
    ):
        old_name = old_folder.title
        old_basename = path.get_basename()
        assert old_basename.startswith(old_name)
        new_basename = f"{new_folder.title}{old_basename[(len(old_name)):]}"
        new_path = AbsolutePath.join(new_folder, new_basename)
        re_path = AbsolutePath.join(new_folder, old_basename)
        if re_path.exists():
            print("Renaming", re_path)
            if new_path.exists():
                raise exceptions.PathAlreadyExists(new_path)
            FileSystem.rename(re_path.path, new_path.path)
            assert not re_path.exists()
            assert new_path.exists()
        return new_path

    def __ensure_identifiers(self):
        id_to_video = {}  # type: Dict[int, Union[VideoState, Video]]
        without_identifiers = []
        for video_state in self.__videos.values():
            if (
                not isinstance(video_state.video_id, int)
                or video_state.video_id in id_to_video
            ):
                without_identifiers.append(video_state)
            else:
                id_to_video[video_state.video_id] = video_state
        next_id = (max(id_to_video) + 1) if id_to_video else 0
        for video_state in without_identifiers:
            video_state.video_id = next_id
            next_id += 1
            id_to_video[video_state.video_id] = video_state
        self.__id_to_video = id_to_video
        return len(without_identifiers)

    def __get_new_video_paths(self):
        all_file_names = []

        file_names = self.__set_videos_states_flags()

        for file_name in file_names:  # type: AbsolutePath
            video_state = None
            if file_name in self.__videos:
                video = self.__videos[file_name]
                if not isinstance(video, Video) or SpecialProperties.all_in(video):
                    video_state = video

            if (
                not video_state
                or video_state.date >= self.__date
                or video_state.runtime.size != video_state.file_size
            ):
                all_file_names.append(file_name.path)

        all_file_names.sort()
        return all_file_names

    def __set_videos_states_flags(self):
        file_paths = self.__check_videos_on_disk()
        for video_state in self.__videos.values():
            info = file_paths.get(video_state.filename, None)
            video_state.runtime.is_file = info is not None
            if info:
                video_state.runtime.mtime = info.mtime
                video_state.runtime.size = info.size
                video_state.runtime.driver_id = info.driver_id
        return file_paths

    def __check_videos_on_disk(self):
        # type: () -> Dict[AbsolutePath, VideoRuntimeInfo]
        paths = {}  # type: Dict[AbsolutePath, VideoRuntimeInfo]
        job_notifier = job_notifications.CollectVideosFromFolders(
            len(self.__folders), self.__notifier
        )
        jobs = [[path, i, job_notifier] for i, path in enumerate(self.__folders)]
        with Profiler(
            title=f"Collect videos ({CPU_COUNT} threads)", notifier=self.__notifier
        ):
            with Pool(CPU_COUNT) as p:
                for local_result in p.imap_unordered(
                    jobs_python.job_collect_videos_stats, jobs
                ):
                    paths.update(local_result)
        self.__notifier.notify(notifications.FinishedCollectingVideos(paths))
        return paths

    def __check_thumbnails_on_disk(self):
        # type: () -> Dict[str, DateModified]
        thumbs = {}
        with Profiler("Collect thumbnails", self.__notifier):
            for entry in FileSystem.scandir(
                self.thumbnail_folder.path
            ):  # type: os.DirEntry
                if entry.path.lower().endswith(f".{THUMBNAIL_EXTENSION}"):
                    name = entry.name
                    thumbs[name[: -(len(THUMBNAIL_EXTENSION) + 1)]] = DateModified(
                        entry.stat().st_mtime
                    )
        return thumbs

    def __notify_missing_thumbnails(self):
        remaining_thumb_videos = [
            video.filename.path
            for video in self.get_videos("readable", "found", "without_thumbnails")
        ]
        self.__notifier.notify(notifications.MissingThumbnails(remaining_thumb_videos))

    def __notify_filename_modified(self):
        self.__notifier.notify(
            notifications.FieldsModified(
                (
                    "title",
                    "title_numeric",
                    "file_title",
                    "file_title_numeric",
                    "disk",
                    "filename",
                )
            )
        )

    # Public methods.

    @Profiler.profile_method()
    def update(self) -> None:
        SpecialProperties.install(self)
        current_date = DateModified.now()

        all_file_names = self.__get_new_video_paths()
        if not all_file_names:
            return

        job_notifier = job_notifications.CollectVideoInfos(
            len(all_file_names), self.__notifier
        )
        jobs = functions.dispatch_tasks(
            all_file_names, CPU_COUNT, [self.folder, job_notifier]
        )
        with Profiler(
            title="Get videos info from JSON (%d threads)" % len(jobs),
            notifier=self.__notifier,
        ):
            results = functions.parallelize(
                backend_raptor.backend_video_infos, jobs, cpu_count=CPU_COUNT
            )

        videos = {}
        unreadable = []
        for arr in results:
            for d in arr:
                file_path = AbsolutePath.ensure(d["f"])
                if len(d) == 2:
                    video_state = VideoState(
                        filename=file_path,
                        size=file_path.get_size(),
                        errors=d["e"],
                        database=self,
                    )
                    unreadable.append(video_state)
                else:
                    video_state = Video.from_dict(d, self)
                    # Get previous properties, if available
                    if file_path in self.__videos and self.__videos[file_path].readable:
                        video_state.properties.update(
                            self.__videos[file_path].properties
                        )
                        video_state.similarity_id = self.__videos[
                            file_path
                        ].similarity_id
                    # Set special properties
                    SpecialProperties.set(video_state)
                videos[file_path] = video_state
                self.__videos.pop(file_path, None)
                stat = FileSystem.stat(file_path.path)
                video_state.runtime.is_file = True
                video_state.runtime.mtime = stat.st_mtime
                video_state.runtime.size = stat.st_size
                video_state.runtime.driver_id = stat.st_dev

        assert len(videos) == len(all_file_names)

        if videos:
            self.__videos.update(videos)
            self.__date = current_date
            self.save()
        if unreadable:
            self.__notifier.notify(
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
        thumb_to_videos = {}  # type: Dict[str, List[Video]]
        thumb_errors = {}

        # Collect videos with and without thumbnails.
        existing_thumb_names = self.__check_thumbnails_on_disk()

        with Profiler("Check videos thumbnails", notifier=self.__notifier):
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
        with Profiler("Check unique thumbnails", notifier=self.__notifier):
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
            nb_videos_no_thumbs, self.__notifier
        )
        thumb_jobs = functions.dispatch_tasks(
            [
                (video.filename.path, video.thumb_name)
                for video in videos_without_thumbs
            ],
            CPU_COUNT,
            [self.__db_folder, self.__thumb_folder.best_path, job_notifier],
        )
        del videos_without_thumbs
        with Profiler(
            title="Get thumbnails from JSON through %d thread(s)" % CPU_COUNT,
            notifier=self.__notifier,
        ):
            results = functions.parallelize(
                backend_raptor.backend_video_thumbnails,
                thumb_jobs,
                cpu_count=CPU_COUNT,
            )

        for arr in results:
            for d in arr:
                assert len(d) == 2 and "f" in d and "e" in d
                file_name = d["f"]
                file_path = AbsolutePath.ensure(file_name)
                thumb_errors[file_name] = d["e"]
                video = self.__videos[file_path]
                video.unreadable_thumbnail = True
                video.runtime.has_thumbnail = False

        if thumb_errors:
            self.__notifier.notify(notifications.VideoThumbnailErrors(thumb_errors))

        self.save()
        self.__notify_missing_thumbnails()

    @Profiler.profile_method()
    def ensure_miniatures(self, returns=False) -> Optional[List[Miniature]]:
        identifiers = set()  # type: Set[AbsolutePath]
        valid_dictionaries = []
        added_miniatures = []
        have_removed = False
        have_added = False

        if self.__miniatures_path.exists():
            with open(self.__miniatures_path.assert_file().path) as miniatures_file:
                json_array = json.load(miniatures_file)
            if not isinstance(json_array, list):
                raise exceptions.InvalidMiniaturesJSON(self.__miniatures_path)
            for dct in json_array:
                identifier = AbsolutePath(dct["i"])
                if (
                    identifier in self.__videos
                    and ImageUtils.DEFAULT_THUMBNAIL_SIZE == (dct["w"], dct["h"])
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
            len(tasks), self.__notifier
        )
        if tasks:
            have_added = True
            jobs = functions.dispatch_tasks(tasks, CPU_COUNT, extra_args=[job_notifier])
            del tasks
            with Profiler("Generating miniatures.", self.__notifier):
                results = functions.parallelize(
                    jobs_python.job_generate_miniatures, jobs, CPU_COUNT
                )
            del jobs
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
                self.__settings.miniature_pixel_distance_radius,
                self.__settings.miniature_group_min_size,
            )
        ] + added_miniatures
        if m_no_groups:
            group_computer = GroupComputer(
                group_min_size=self.__settings.miniature_group_min_size,
                pixel_distance_radius=self.__settings.miniature_pixel_distance_radius,
            )
            for dm in group_computer.batch_compute_groups(
                m_no_groups, notifier=self.__notifier
            ):
                m_dict[dm.miniature_identifier].set_group_signature(
                    self.__settings.miniature_pixel_distance_radius,
                    self.__settings.miniature_group_min_size,
                    len(dm.pixel_groups),
                )

        if have_removed or have_added:
            with open(self.__miniatures_path.path, "w") as output_file:
                json.dump([m.to_dict() for m in available_miniatures], output_file)

        self.__notifier.notify(notifications.NbMiniatures(len(available_miniatures)))

        if returns:
            miniatures = []
            for video in available_videos:
                miniature = m_dict[video.filename.path]
                miniature.video_id = video.video_id
                miniatures.append(miniature)
            return miniatures

    def rename(self, new_name) -> None:
        old_db_folder = self.__db_folder
        old_thumb_folder = self.__thumb_folder
        old_json_path = self.__json_path
        old_miniature_path = self.__miniatures_path
        old_log_path = self.__log_path

        new_name = new_name.strip()
        if new_name == self.__db_folder.title:
            return
        if functions.has_discarded_characters(new_name):
            raise exceptions.InvalidDatabaseName(new_name)

        new_db_folder = AbsolutePath.join(old_db_folder.get_directory(), new_name)
        if new_db_folder.exists():
            raise exceptions.DatabaseAlreadyExists(new_db_folder)
        FileSystem.rename(old_db_folder.path, new_db_folder.path)
        assert not old_db_folder.exists()
        assert new_db_folder.isdir()

        self.__db_folder = new_db_folder
        self.__thumb_folder = self.__transfer_db_path(
            old_thumb_folder, old_db_folder, new_db_folder
        )
        self.__json_path = self.__transfer_db_path(
            old_json_path, old_db_folder, new_db_folder
        )
        self.__miniatures_path = self.__transfer_db_path(
            old_miniature_path, old_db_folder, new_db_folder
        )
        self.__log_path = self.__transfer_db_path(
            old_log_path, old_db_folder, new_db_folder
        )

        self.__notifier.set_log_path(self.__log_path.path)

    def set_folders(self, folders) -> None:
        folders = sorted(AbsolutePath.ensure(folder) for folder in folders)
        if folders == sorted(self.__folders):
            return
        folders_tree = PathTree(folders)
        for video in self.__videos.values():
            video.discarded = not folders_tree.in_folders(video.filename)
        self.__folders = set(folders)
        self.save()

    def dismiss_similarity(self, video_id: int):
        video = self.__get_video_from_id(video_id)
        video.similarity_id = -1
        self.save()
        self.__notifier.notify(notifications.FieldsModified(["similarity_id"]))

    def reset_similarity(self, video_id: int):
        video = self.__get_video_from_id(video_id)
        video.similarity_id = None
        self.save()
        self.__notifier.notify(notifications.FieldsModified(["similarity_id"]))

    def change_video_file_title(self, video_id: int, new_title: str) -> None:
        video = self.__get_video_from_id(video_id)
        if video.filename.file_title != new_title:
            if functions.has_discarded_characters(new_title):
                raise exceptions.InvalidFileName(new_title)
            new_filename = video.filename.new_title(new_title)
            del self.__videos[video.filename]
            self.__videos[new_filename] = video
            video.filename = new_filename
            self.save()
            self.__notify_filename_modified()

    def change_video_path(self, video_id: int, path: AbsolutePath) -> AbsolutePath:
        video = self.__get_video_from_id(video_id)
        path = AbsolutePath.ensure(path)
        assert video.filename != path
        assert path.isfile()
        old_filename = video.filename
        del self.__videos[video.filename]
        self.__videos[path] = video
        video.filename = path
        self.save()
        self.__notify_filename_modified()
        return old_filename

    def delete_video(self, video_id: int, save=True) -> AbsolutePath:
        video = self.__id_to_video[video_id]
        video.filename.delete()
        self.__videos.pop(video.filename, None)
        self.__id_to_video.pop(video.video_id, None)
        if isinstance(video, Video):
            video.thumbnail_path.delete()
        if save:
            self.save()
        self.__notifier.notify(notifications.VideoDeleted(video))
        self.__notifier.notify(notifications.FieldsModified(["move_id", "quality"]))
        return video.filename

    def add_prop_type(self, prop: PropType, save: bool = True) -> None:
        if prop.name in self.__prop_types:
            raise exceptions.PropertyAlreadyExists(prop.name)
        self.__prop_types[prop.name] = prop
        if save:
            self.save()

    def rename_prop_type(self, old_name, new_name) -> None:
        if old_name in self.__prop_types:
            if new_name in self.__prop_types:
                raise exceptions.PropertyAlreadyExists(new_name)
            prop_type = self.__prop_types.pop(old_name)
            prop_type.name = new_name
            self.__prop_types[new_name] = prop_type
            for video in self.get_videos("readable"):
                if old_name in video.properties:
                    video.properties[new_name] = video.properties.pop(old_name)
            self.save()

    def convert_prop_to_unique(self, name) -> None:
        if name in self.__prop_types:
            prop_type = self.__prop_types[name]
            if not prop_type.multiple:
                raise exceptions.PropertyAlreadyUnique(name)
            for video in self.get_videos("readable"):
                if name in video.properties and len(video.properties[name]) > 1:
                    raise exceptions.PropertyToUniqueError(name, video)
            prop_type.multiple = False
            for video in self.get_videos("readable"):
                if name in video.properties:
                    if video.properties[name]:
                        video.properties[name] = video.properties[name][0]
                    else:
                        del video.properties[name]
            self.save()

    def convert_prop_to_multiple(self, name) -> None:
        if name in self.__prop_types:
            prop_type = self.__prop_types[name]
            if prop_type.multiple:
                raise exceptions.PropertyAlreadyMultiple(name)
            prop_type.multiple = True
            for video in self.get_videos("readable"):
                if name in video.properties:
                    video.properties[name] = [video.properties[name]]
            self.save()

    def remove_prop_type(self, name) -> None:
        if name in self.__prop_types:
            del self.__prop_types[name]
            for video in self.get_videos("readable"):
                video.remove_property(name)
            self.save()

    def has_prop_type(self, name) -> bool:
        return name in self.__prop_types

    def get_prop_type(self, name: str) -> PropType:
        return self.__prop_types[name]

    def get_prop_types(self) -> Iterable[PropType]:
        return self.__prop_types.values()

    def set_video_properties(self, video_id: int, properties) -> Set[str]:
        video = self.__get_video_from_id(video_id)
        modified = video.set_properties(properties)
        self.save()
        self.__notifier.notify(notifications.PropertiesModified(modified))
        return modified

    def refresh(self, ensure_miniatures=False) -> None:
        with Profiler("Reset thumbnail errors"):
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
            self.__notifier.notify(notifications.PropertiesModified([name]))
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
            self.__notifier.notify(
                notifications.PropertiesModified([old_name, new_name])
            )

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
            self.__notifier.notify(notifications.PropertiesModified([name]))
        return modified

    def edit_property_for_videos(
        self,
        name: str,
        video_indices: List[int],
        values_to_add: list,
        values_to_remove: list,
    ) -> None:
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
            video = self.__id_to_video[video_id]
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
        self.__notifier.notify(notifications.PropertiesModified([name]))

    def count_property_values(
        self, name: str, video_indices: List[int]
    ) -> Dict[object, int]:
        prop_type = self.get_prop_type(name)
        value_to_count = {}
        video_indices = set(video_indices)
        for video_id in video_indices:
            video = self.__id_to_video[video_id]
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
        self.__notifier.notify(notifications.PropertiesModified([prop_name]))

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
            self.__notifier.notify(
                notifications.PropertiesModified([from_property, to_property])
            )

        return len(modified)

    def move_video_entry(self, from_id, to_id):
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
        self.delete_video(from_id)

    def set_message(self, message: str):
        self.__message = message

    def flush_message(self):
        message = self.__message
        self.__message = None
        return message

    def get_predictor(self, prop_name):
        return self.__predictors.get(prop_name, None)

    def set_predictor(self, prop_name: str, theta: List[float]):
        self.__predictors[prop_name] = theta

    # Videos access and edition

    def get_videos(self, *flags, **forced_flags) -> List[Union[VideoState, Video]]:
        return self.__cache.get(*flags, **forced_flags)

    def query(self, required: Dict[str, bool]) -> List[Union[VideoState, Video]]:
        videos = self.__videos.values()
        return (
            [
                video
                for video in videos
                if all(getattr(video, flag) is required[flag] for flag in required)
            ]
            if required
            else list(videos)
        )

    def __get_video_from_id(self, video_id: int) -> Video:
        video = self.__id_to_video[video_id]
        assert isinstance(video, Video)
        return video

    def has_video_id(self, video_id: int) -> bool:
        return video_id in self.__id_to_video

    def get_video_string(self, video_id: int) -> str:
        return str(self.__id_to_video[video_id])

    def get_video_fields(self, video_id: int, fields: Sequence[str]) -> namedtuple:
        cls = namedtuple("cls", fields)
        vid = self.__id_to_video[video_id]
        return cls(**{field: getattr(vid, field) for field in fields})

    def get_video_field(self, video_id: int, field: str):
        return getattr(self.__id_to_video[video_id], field)

    def get_video_filename(self, video_id: int) -> AbsolutePath:
        return self.__id_to_video[video_id].filename

    def get_videos_field(self, indices: Iterable[int], field: str) -> Iterable:
        return (getattr(self.__id_to_video[video_id], field) for video_id in indices)

    def set_videos_field_with_same_value(
        self, indices: Iterable[int], field: str, value
    ) -> None:
        for video_id in indices:
            setattr(self.__id_to_video[video_id], field, value)

    def set_videos_field(self, indices: Iterable[int], field, values: Iterable) -> None:
        for video_id, value in zip(indices, values):
            setattr(self.__id_to_video[video_id], field, value)
