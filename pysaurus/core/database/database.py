import itertools
import os
from typing import Dict, Iterable, List, Optional, Set, Union

import ujson as json

from pysaurus.core import exceptions, functions, notifications
from pysaurus.core.components import (
    AbsolutePath,
    DateModified,
    FilePath,
    PathType,
)
from pysaurus.core.constants import THUMBNAIL_EXTENSION, CPU_COUNT
from pysaurus.core.database import path_utils, jobs_python
from pysaurus.core.database.db_settings import DbSettings
from pysaurus.core.database.db_video_attribute import (
    QualityAttribute,
    PotentialMoveAttribute,
)
from pysaurus.core.database.properties import PropType
from pysaurus.core.database.video import Video
from pysaurus.core.database.video_runtime_info import VideoRuntimeInfo
from pysaurus.core.database.video_state import VideoState
from pysaurus.core.miniature_tools.group_computer import GroupComputer
from pysaurus.core.miniature_tools.miniature import Miniature
from pysaurus.core.modules import ImageUtils, System, FileSystem
from pysaurus.core.notifier import Notifier, DEFAULT_NOTIFIER
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler

SPECIAL_PROPERTIES = [PropType("<error>", "", True)]


def new_sub_file(folder: AbsolutePath, extension: str):
    return FilePath(folder, folder.title, extension)


def new_sub_folder(folder: AbsolutePath, suffix: str, sep="."):
    return AbsolutePath.join(folder, f"{folder.title}{sep}{suffix}")


FILENAME_RELATED_FIELDS = (
    "title",
    "title_numeric",
    "file_title",
    "file_title_numeric",
    "disk",
    "filename",
)


class Database:
    __slots__ = (
        "__db_folder",
        "__thumb_folder",
        "__json_path",
        "__miniatures_path",
        "__log_path",
        "__settings",
        "__date",
        "__folders",
        "__videos",
        "__unreadable",
        "__discarded",
        "__prop_types",
        "__notifier",
        "__id_to_video",
        "sys_is_case_insensitive",
        "quality_attribute",
        "moves_attribute",
        "__prop_parser",
        "__save_id",
    )

    def __init__(self, path, folders=None, clear_old_folders=False, notifier=None):
        # type: (PathType, Iterable[PathType], bool, Notifier) -> None
        # Paths
        self.__db_folder = AbsolutePath.ensure_directory(path)
        self.__thumb_folder = new_sub_folder(self.__db_folder, "thumbnails").mkdir()
        self.__json_path = new_sub_file(self.__db_folder, "json")
        self.__miniatures_path = new_sub_file(self.__db_folder, "miniatures.json")
        self.__log_path = new_sub_file(self.__db_folder, "log")
        # Database data
        self.__settings = DbSettings()
        self.__date = DateModified.now()
        self.__folders = set()  # type: Set[AbsolutePath]
        self.__videos = {}  # type: Dict[AbsolutePath, Video]
        self.__unreadable = {}  # type: Dict[AbsolutePath, VideoState]
        self.__discarded = {}  # type: Dict[AbsolutePath, VideoState]
        self.__prop_types = {}  # type: Dict[str, PropType]
        # RAM data
        self.__notifier = notifier or DEFAULT_NOTIFIER
        self.__id_to_video = {}  # type: Dict[int, Union[VideoState, Video]]
        self.sys_is_case_insensitive = System.is_case_insensitive(self.__db_folder.path)
        self.__prop_parser = {}  # type: Dict[str, callable]
        self.__save_id = 0
        self.quality_attribute = QualityAttribute(self)
        self.moves_attribute = PotentialMoveAttribute(self)
        # Load database
        self.__notifier.set_log_path(self.__log_path.path)

        self.__load(folders, clear_old_folders)
        # Load VideoInterval object to compute videos quality.
        # Set special properties.
        self.__set_special_properties()
        self.__register_special_property_parsers()

    # Properties.

    nb_entries = property(
        lambda self: len(self.__videos) + len(self.__unreadable) + len(self.__discarded)
    )
    nb_discarded = property(lambda self: len(self.__discarded))
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
            if not self.__json_path.isfile():
                raise exceptions.NotFileError(self.__json_path)
            with open(self.__json_path.path, "r") as output_file:
                json_dict = json.load(output_file)
            if not isinstance(json_dict, dict):
                raise exceptions.PysaurusError(
                    "Database file does not contain a dictionary."
                )
        else:
            json_dict = {}

        # Parsing settings.
        self.__settings.update(json_dict.get("settings", {}))

        # Parsing date.
        if "date" in json_dict:
            self.__date = DateModified(json_dict["date"])

        # Parsing folders.
        if not clear_old_folders:
            for path in json_dict.get("folders", ()):
                self.__folders.add(AbsolutePath.ensure(path))
        if folders:
            for path in folders:
                self.__folders.add(AbsolutePath.ensure(path))

        folders_tree = PathTree(self.__folders)

        # Parsing video property types.
        for prop_dict in json_dict.get("prop_types", ()):
            self.add_prop_type(PropType.from_dict(prop_dict), save=False)

        # Parsing videos.
        for video_dict in json_dict.get("videos", ()):
            if video_dict["U"]:
                video_state = VideoState.from_dict(video_dict, self)
                destination = self.__unreadable
            else:
                video_state = Video.from_dict(video_dict, self)
                destination = self.__videos
            if folders_tree.in_folders(video_state.filename):
                destination[video_state.filename] = video_state
            else:
                self.__discarded[video_state.filename] = video_state

        if self.__ensure_identifiers():
            self.__to_save(ensure_identifiers=False)
        self.__notifier.notify(notifications.DatabaseLoaded(self))

    def __to_save(self, ensure_identifiers=True):
        if ensure_identifiers:
            self.__ensure_identifiers()
        self.__save_id += 1
        self.save()

    def save(self):
        # Save database.
        json_output = {
            "settings": self.__settings.to_dict(),
            "date": self.__date.time,
            "folders": sorted(folder.path for folder in self.__folders),
            "videos": sorted(
                (
                    video.to_dict()
                    for dct in (self.__videos, self.__unreadable, self.__discarded)
                    for video in dct.values()
                ),
                key=lambda dct: dct["f"],
            ),
            "prop_types": [prop.to_dict() for prop in self.__prop_types.values()],
        }
        # functions.assert_data_is_serializable(json_output)
        with open(self.__json_path.path, "w") as output_file:
            json.dump(json_output, output_file)
        self.__notifier.notify(notifications.DatabaseSaved(self))

    def set_folders(self, folders):
        folders = sorted(AbsolutePath.ensure(folder) for folder in folders)
        if folders == sorted(self.__folders):
            return
        folders_tree = PathTree(folders)
        videos = {}
        unreadable = {}
        discarded = {}
        for video in itertools.chain(
            self.__videos.values(),
            self.__unreadable.values(),
            self.__discarded.values(),
        ):
            if folders_tree.in_folders(video.filename):
                if video.unreadable:
                    unreadable[video.filename] = video
                else:
                    videos[video.filename] = video
            else:
                discarded[video.filename] = video
        self.__folders = set(folders)
        self.__videos = videos
        self.__unreadable = unreadable
        self.__discarded = discarded
        self.__to_save()

    def __ensure_identifiers(self):
        id_to_video = {}  # type: Dict[int, Union[VideoState, Video]]
        without_identifiers = []
        for source in (self.__videos, self.__unreadable):
            for video_state in source.values():
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

    def __set_videos_states_flags(self):
        file_paths = self.__check_videos_on_disk()
        for dictionaries in (self.__videos, self.__unreadable):
            for video_state in dictionaries.values():
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
        jobs = functions.dispatch_tasks(sorted(self.__folders), CPU_COUNT)
        with Profiler(
            title=f"Collect videos ({CPU_COUNT} threads)", notifier=self.__notifier
        ):
            results = functions.parallelize(
                jobs_python.job_collect_videos_info, jobs, CPU_COUNT
            )
        for local_result in results:  # type: Dict[AbsolutePath, VideoRuntimeInfo]
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
                    if self.sys_is_case_insensitive:
                        name = name.lower()
                    thumbs[name[: -(len(THUMBNAIL_EXTENSION) + 1)]] = DateModified(
                        entry.stat().st_mtime
                    )
        return thumbs

    def __notify_missing_thumbnails(self):
        remaining_thumb_videos = []
        for video in self.__videos.values():
            if video.exists and not video.has_thumbnail:
                remaining_thumb_videos.append(video.filename.path)
        self.__notifier.notify(notifications.MissingThumbnails(remaining_thumb_videos))

    def __set_special_properties(self):
        to_save = False
        for expected in SPECIAL_PROPERTIES:
            if (
                not self.has_prop_type(expected.name)
                or self.get_prop_type(expected.name) != expected
            ):
                self.remove_prop_type(expected.name)
                self.add_prop_type(expected)
                to_save = True
        if to_save:
            self.__to_save()

    def __register_special_property_parsers(self):
        for prop in SPECIAL_PROPERTIES:
            self.__prop_parser[prop.name] = getattr(
                self, f"_set_v_prop_{prop.name[1:-1]}"
            )

    @staticmethod
    def _set_v_prop_error(video: Video, prop: PropType):
        video.properties[prop.name] = sorted(video.errors)

    # Public methods.

    @Profiler.profile_method()
    def update(self):

        self.__set_special_properties()

        current_date = DateModified.now()
        all_file_names = self.get_new_video_paths()

        jobn = notifications.Jobs.videos(len(all_file_names), self.__notifier)
        if not all_file_names:
            return
        jobs = []
        for index, (file_names, job_id) in enumerate(
            functions.dispatch_tasks(all_file_names, CPU_COUNT)
        ):
            input_file_path = FilePath(self.__db_folder, str(index), "list")
            output_file_path = FilePath(self.__db_folder, str(index), "json")

            with open(input_file_path.path, "wb") as file:
                for file_name in file_names:
                    file.write(("%s\n" % file_name).encode())

            jobs.append(
                (
                    input_file_path.path,
                    output_file_path.path,
                    len(file_names),
                    job_id,
                    jobn,
                )
            )

        with Profiler(
            title="Get videos info from JSON (%d threads)" % len(jobs),
            notifier=self.__notifier,
        ):
            counts_loaded = functions.parallelize(
                jobs_python.job_video_to_json, jobs, cpu_count=CPU_COUNT
            )

        videos = {}
        unreadable = {}
        for job in jobs:
            list_file_path = AbsolutePath.ensure(job[0])
            json_file_path = AbsolutePath.ensure(job[1])
            assert json_file_path.isfile()
            with open(json_file_path.path, encoding="utf-8") as file:
                arr = json.load(file)
            for d in arr:
                file_path = AbsolutePath.ensure(d["f"])
                if len(d) == 2:
                    video_state = VideoState(
                        filename=file_path,
                        size=file_path.get_size(),
                        errors=d["e"],
                        database=self,
                    )
                    unreadable[file_path] = video_state
                    self.__videos.pop(file_path, None)
                else:
                    video_state = Video.from_dict(d, self)

                    # Get previous properties, if available
                    if file_path in self.__videos:
                        video_state.properties.update(
                            self.__videos[file_path].properties
                        )

                    # Set special properties
                    for prop in SPECIAL_PROPERTIES:
                        self.__prop_parser[prop.name](video_state, prop)

                    videos[file_path] = video_state
                    self.__unreadable.pop(file_path, None)
                stat = FileSystem.stat(file_path.path)
                video_state.runtime.is_file = True
                video_state.runtime.mtime = stat.st_mtime
                video_state.runtime.size = stat.st_size
                video_state.runtime.driver_id = stat.st_dev

            list_file_path.delete()
            json_file_path.delete()
        assert sum(counts_loaded) == len(videos)
        assert len(videos) + len(unreadable) == len(all_file_names)

        if videos:
            self.__videos.update(videos)
        if unreadable:
            self.__unreadable.update(unreadable)
        if videos or unreadable:
            self.__date = current_date
            self.__to_save()
        if unreadable:
            self.__notifier.notify(
                notifications.VideoInfoErrors(
                    {
                        file_name: video_state.errors
                        for file_name, video_state in unreadable.items()
                    }
                )
            )

    @Profiler.profile_method()
    def ensure_thumbnails(self):
        valid_thumb_names = set()
        videos_without_thumbs = []
        thumb_to_videos = {}  # type: Dict[str, List[Video]]
        thumb_errors = {}
        thumb_jobs = []

        # Collect videos with and without thumbnails.
        existing_thumb_names = self.__check_thumbnails_on_disk()

        with Profiler("Check videos thumbnails", notifier=self.__notifier):
            for video in self.__videos.values():
                thumb_name = video.ensure_thumbnail_name()
                if not video.exists:
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

        jobn = notifications.Jobs.thumbnails(nb_videos_no_thumbs, self.__notifier)
        if not videos_without_thumbs:
            self.__notify_missing_thumbnails()
            return

        for video in videos_without_thumbs:
            base_thumb_name = video.ensure_thumbnail_name()
            thumb_name_index = 0
            thumb_name = base_thumb_name
            while thumb_name in valid_thumb_names:
                thumb_name = "%s_%d" % (base_thumb_name, thumb_name_index)
                thumb_name_index += 1
            video.thumb_name = thumb_name
            video.runtime.has_thumbnail = True
            valid_thumb_names.add(thumb_name)
        del valid_thumb_names
        self.__to_save()

        dispatched_thumb_jobs = functions.dispatch_tasks(
            videos_without_thumbs, CPU_COUNT
        )
        del videos_without_thumbs
        for index, (job_videos, job_id) in enumerate(dispatched_thumb_jobs):
            input_file_path = FilePath(self.__db_folder, str(index), "thumbnails.list")
            output_file_path = FilePath(self.__db_folder, str(index), "thumbnails.json")

            with open(input_file_path.path, "wb") as file:
                for video in job_videos:
                    file.write(
                        (
                            "%s\t%s\t%s\t\n"
                            % (video.filename, self.__thumb_folder, video.thumb_name)
                        ).encode()
                    )

            thumb_jobs.append(
                (
                    input_file_path.path,
                    output_file_path.path,
                    len(job_videos),
                    job_id,
                    jobn,
                )
            )

        with Profiler(
            title="Get thumbnails from JSON through %d thread(s)" % len(thumb_jobs),
            notifier=self.__notifier,
        ):
            counts_loaded = functions.parallelize(
                jobs_python.job_video_thumbnails_to_json,
                thumb_jobs,
                cpu_count=CPU_COUNT,
            )

        for job in thumb_jobs:
            list_file_path = AbsolutePath.ensure(job[0])
            json_file_path = AbsolutePath.ensure(job[1])
            assert json_file_path.isfile()

            with open(json_file_path.path, encoding="utf-8") as file:
                arr = json.load(file)
            for d in arr:
                if d is not None:
                    assert len(d) == 2 and "f" in d and "e" in d
                    file_name = d["f"]
                    file_path = AbsolutePath.ensure(file_name)
                    thumb_errors[file_name] = d["e"]
                    video = self.__videos[file_path]
                    video.unreadable_thumbnail = True
                    video.runtime.has_thumbnail = False

            list_file_path.delete()
            json_file_path.delete()

        assert sum(counts_loaded) + len(thumb_errors) == nb_videos_no_thumbs

        if thumb_errors:
            self.__notifier.notify(notifications.VideoThumbnailErrors(thumb_errors))

        self.__notify_missing_thumbnails()
        self.__to_save()

    @Profiler.profile_method()
    def ensure_miniatures(self, returns=False):
        # type: (bool) -> Optional[List[Video]]

        identifiers = set()  # type: Set[AbsolutePath]
        valid_dictionaries = []
        added_miniatures = []
        have_removed = False
        have_added = False

        if self.__miniatures_path.exists():
            if not self.__miniatures_path.isfile():
                raise exceptions.NotFileError(self.__miniatures_path)
            with open(self.__miniatures_path.path, "r") as miniatures_file:
                json_array = json.load(miniatures_file)
            if not isinstance(json_array, list):
                raise exceptions.PysaurusError(
                    "Miniatures file does not contain a list."
                )
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

        jobn = notifications.Jobs.miniatures(len(tasks), self.__notifier)
        if tasks:
            have_added = True
            jobs = functions.dispatch_tasks(tasks, CPU_COUNT, extra_args=[jobn])
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
        m_dict = {m.identifier: m for m in available_miniatures}

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
            for video in available_videos:
                video.miniature = m_dict[video.filename.path]
            return available_videos

    def save_miniatures(self, miniatures: List[Miniature]):
        with open(self.__miniatures_path.path, "w") as output_file:
            json.dump([m.to_dict() for m in miniatures], output_file)

    def list_files(self, output_name):
        with open(output_name, "wb") as file:
            file.write("# Videos\n".encode())
            for file_name in sorted(self.__videos):
                file.write(("%s\n" % str(file_name)).encode())
            file.write("# Unreadable\n".encode())
            for file_name in sorted(self.__unreadable):
                file.write(("%s\n" % str(file_name)).encode())
            file.write("# Discarded\n".encode())
            for file_name in sorted(self.__discarded):
                file.write(("%s\n" % str(file_name)).encode())

    def reset(self, reset_thumbnails=False, reset_miniatures=False):
        self.__videos.clear()
        self.__unreadable.clear()
        self.__discarded.clear()
        self.__json_path.delete()
        if reset_miniatures:
            self.__miniatures_path.delete()
        if reset_thumbnails:
            self.__thumb_folder.delete()

    def change_video_file_title(self, video, new_title):
        # type: (VideoState, str) -> None
        discarded_characters = r"@#\\/?$"
        if video.filename.file_title != new_title:
            if any(c in new_title for c in discarded_characters):
                raise OSError("Characters not allowed: %s" % discarded_characters)
            new_filename = video.filename.new_title(new_title)
            if video.filename in self.__videos:
                video: Video
                del self.__videos[video.filename]
                self.__videos[new_filename] = video
            elif video.filename in self.__unreadable:
                del self.__unreadable[video.filename]
                self.__unreadable[new_filename] = video
            video.filename = new_filename
            self.__to_save()
            self.__notifier.notify(
                notifications.FieldsModified(FILENAME_RELATED_FIELDS)
            )

    def change_video_path(self, video: Video, path: AbsolutePath) -> AbsolutePath:
        path = AbsolutePath.ensure(path)
        assert video.filename != path
        assert path.isfile()
        for dct in (self.__videos, self.__unreadable, self.__discarded):
            if video.filename in dct:
                old_filename = video.filename
                del dct[video.filename]
                dct[path] = video
                video.filename = path
                # TODO DB update will always recheck this video, as path mtime changed.
                self.__to_save()
                self.__notifier.notify(
                    notifications.FieldsModified(FILENAME_RELATED_FIELDS)
                )
                return old_filename

    def remove_videos_not_found(self):
        nb_removed = 0
        for video in list(self.__videos.values()):
            if not video.filename.isfile():
                self.delete_video(video, save=False)
                nb_removed += 1
        if nb_removed:
            self.__notifier.notify(notifications.VideosNotFoundRemoved(nb_removed))
            self.__to_save()

    def get_video_from_id(self, video_id: int, required=True) -> Optional[Video]:
        if (
            video_id in self.__id_to_video
            and self.__id_to_video[video_id].filename in self.__videos
        ):
            return self.__id_to_video[video_id]
        if required:
            raise exceptions.UnknownVideoID(video_id)
        return None

    def get_unreadable_from_id(self, video_id, required=True):
        # type: (int, bool) -> Optional[VideoState]
        if (
            video_id in self.__id_to_video
            and self.__id_to_video[video_id].filename in self.__unreadable
        ):
            return self.__id_to_video[video_id]
        if required:
            raise exceptions.UnknownVideoID(video_id)
        return None

    def get_from_id(self, video_id, required=True):
        # type: (int, bool) -> Optional[VideoState]
        if video_id in self.__id_to_video:
            return self.__id_to_video[video_id]
        if required:
            raise exceptions.UnknownVideoID(video_id)
        return None

    def get_unreadable_from_filename(self, filename, required=True):
        # type: (PathType, bool) -> Optional[VideoState]
        filename = AbsolutePath.ensure(filename)
        if filename in self.__unreadable:
            return self.__unreadable[filename]
        if required:
            raise exceptions.UnknownVideoFilename(filename)
        return None

    def delete_video(self, video, save=True):
        # type: (VideoState, bool) -> AbsolutePath
        video.filename.delete()
        self.__videos.pop(video.filename, None)
        self.__unreadable.pop(video.filename, None)
        self.__discarded.pop(video.filename, None)
        self.__id_to_video.pop(video.video_id, None)
        if isinstance(video, Video):
            video.thumbnail_path.delete()
        if save:
            self.__to_save()
        self.__notifier.notify(notifications.VideoDeleted(video))
        return video.filename

    def get_new_video_paths(self):
        all_file_names = []

        file_names = self.__set_videos_states_flags()

        for file_name in file_names:  # type: AbsolutePath
            video_state = None
            if file_name in self.__videos:
                video = self.__videos[file_name]
                if all(prop.name in video.properties for prop in SPECIAL_PROPERTIES):
                    video_state = video
            elif file_name in self.__unreadable:
                video_state = self.__unreadable[file_name]

            if (
                not video_state
                or video_state.date >= self.__date
                or video_state.runtime.size != video_state.file_size
            ):
                all_file_names.append(file_name.path)

        all_file_names.sort()
        return all_file_names

    def get_video_from_filename(self, filename, required=True):
        # type: (PathType, bool) -> Optional[Video]
        filename = AbsolutePath.ensure(filename)
        if filename in self.__videos:
            return self.__videos[filename]
        if required:
            raise exceptions.UnknownVideoFilename(filename)
        return None

    def add_prop_type(self, prop: PropType, save: bool = True):
        if prop.name in self.__prop_types:
            raise ValueError("Property name already exists: %s" % prop.name)
        self.__prop_types[prop.name] = prop
        if save:
            self.__to_save()

    def rename_prop_type(self, old_name, new_name):
        if old_name in self.__prop_types:
            if new_name in self.__prop_types:
                raise ValueError(f"Property new name already exists: {new_name}")
            prop_type = self.__prop_types.pop(old_name)
            prop_type.name = new_name
            self.__prop_types[new_name] = prop_type
            for video in self.__videos.values():
                if old_name in video.properties:
                    video.properties[new_name] = video.properties.pop(old_name)
            self.__to_save()

    def convert_prop_to_unique(self, name):
        if name in self.__prop_types:
            prop_type = self.__prop_types[name]
            if not prop_type.multiple:
                raise ValueError(f'"{name}" is already a unique property')
            for video in self.__videos.values():
                if name in video.properties and len(video.properties[name]) > 1:
                    raise ValueError(
                        f"""A video has multiple values for this property.
Video: {video.filename}
Values: {', '.join(str(v) for v in video.properties[name])}
Make sure any video has at most 1 value for this property before making it unique."""
                    )
            prop_type.multiple = False
            for video in self.__videos.values():
                if name in video.properties:
                    if video.properties[name]:
                        video.properties[name] = video.properties[name][0]
                    else:
                        del video.properties[name]
            self.__to_save()

    def convert_prop_to_multiple(self, name):
        if name in self.__prop_types:
            prop_type = self.__prop_types[name]
            if prop_type.multiple:
                raise ValueError(f'"{name}" is already a multiple property')
            prop_type.multiple = True
            for video in self.__videos.values():
                if name in video.properties:
                    video.properties[name] = [video.properties[name]]
            self.__to_save()

    def remove_prop_type(self, name):
        if name in self.__prop_types:
            del self.__prop_types[name]
            for video in self.__videos.values():
                video.remove_property(name)
            self.__to_save()

    def has_prop_type(self, name):
        return name in self.__prop_types

    def get_prop_type(self, name: str) -> PropType:
        return self.__prop_types[name]

    def get_prop_types(self) -> Iterable[PropType]:
        return self.__prop_types.values()

    def set_video_properties(self, video: Video, properties):
        modified = video.set_properties(properties)
        self.__to_save()
        self.__notifier.notify(notifications.PropertiesModified(modified))
        return modified

    def refresh(self, ensure_miniatures=False):
        with Profiler("Reset thumbnail errors"):
            for video in self.get_videos("readable", "found", "without_thumbnails"):
                video.unreadable_thumbnail = False
        self.update()
        self.ensure_thumbnails()
        if ensure_miniatures:
            self.ensure_miniatures()

    def delete_property_value(self, videos, name, values):
        # type: (Iterable[Video], str, List) -> List[Video]
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
            self.__to_save()
            self.__notifier.notify(notifications.PropertiesModified([name]))
        return modified

    def edit_property_value(self, videos, name, old_values, new_value):
        # type: (Iterable[Video], str, List, object) -> bool
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
            self.__to_save()
            self.__notifier.notify(notifications.PropertiesModified([name]))
        return modified

    def move_property_value(self, videos, old_name, values, new_name):
        # type: (Iterable[Video], str, List, str) -> List[Video]
        assert len(values) == 1, values
        value = values[0]
        prop_type = self.get_prop_type(new_name)
        prop_type.validate([value] if prop_type.multiple else value)
        videos = self.delete_property_value(videos, old_name, [value])
        if prop_type.multiple:
            for video in videos:
                new_values = set(video.properties.get(new_name, ()))
                new_values.add(value)
                video.properties[new_name] = sorted(new_values)
        else:
            for video in videos:
                video.properties[new_name] = value
        if videos:
            self.__to_save()
            self.__notifier.notify(
                notifications.PropertiesModified([old_name, new_name])
            )
        return videos

    def edit_property_for_videos(
        self, name, video_indices, values_to_add, values_to_remove
    ):
        # type: (str, List[int], List, List) -> None
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
        self.__to_save()
        self.__notifier.notify(notifications.PropertiesModified([name]))

    def count_property_values(self, name, video_indices):
        # type: (str, List[int]) -> Dict[object, int]
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

    def fill_property_with_terms(self, videos, prop_name, only_empty=False):
        # type: (Iterable[Video], str, bool) -> None
        prop_type = self.get_prop_type(prop_name)
        assert prop_type.multiple
        assert prop_type.type is str
        for video in videos:
            if only_empty and video.properties.get(prop_name, None):
                continue
            values = video.terms(as_set=True)
            values.update(video.properties.get(prop_name, ()))
            video.properties[prop_name] = prop_type(values)
        self.__to_save()
        self.__notifier.notify(notifications.PropertiesModified([prop_name]))

    def move_concatenated_prop_val(self, videos, path, from_property, to_property):
        # type: (Iterable[Video], List, str, str) -> int
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
            self.__to_save()
            self.__notifier.notify(
                notifications.PropertiesModified([from_property, to_property])
            )

        return len(modified)

    @classmethod
    @Profiler.profile()
    def load_from_list_file_path(
        cls,
        list_file_path,
        notifier=None,
        update=True,
        ensure_miniatures=True,
        reset=False,
        clear_old_folders=False,
    ):
        paths = path_utils.load_path_list_file(list_file_path)
        database_folder = list_file_path.get_directory()
        database = cls(
            path=database_folder,
            folders=paths,
            notifier=notifier,
            clear_old_folders=clear_old_folders,
        )
        if reset:
            database.reset()
        if update:
            database.refresh(ensure_miniatures)
        return database

    def get_videos(self, source, *flags, **forced_flags):
        if source == "readable":
            videos = self.__videos.values()
        else:
            assert source == "unreadable"
            videos = self.__unreadable.values()
        required = {flag: True for flag in flags}
        required.update(forced_flags)
        return (
            [
                video
                for video in videos
                if all(getattr(video, flag) is required[flag] for flag in required)
            ]
            if required
            else list(videos)
        )

    def get_valid_videos(self):
        return self.get_videos("readable", "found", "with_thumbnails")

    def get_readable_videos(self) -> Iterable[Video]:
        return self.__videos.values()

    def get_all_videos(self):
        return itertools.chain(self.__videos.values(), self.__unreadable.values())
