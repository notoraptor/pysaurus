from typing import Dict, Iterable, List, Optional, Set

from pysaurus.application import exceptions
from pysaurus.core import notifications
from pysaurus.core.components import AbsolutePath, DateModified, PathType
from pysaurus.core.notifier import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database.db_cache import DbCache
from pysaurus.database.db_settings import DbSettings
from pysaurus.database.db_video_attribute import (
    PotentialMoveAttribute,
    QualityAttribute,
)
from pysaurus.database.json_backup import JsonBackup
from pysaurus.database.properties import PropType
from pysaurus.database.video import Video


class JsonDatabase:
    __slots__ = (
        "settings",
        "date",
        "folders",
        "videos",
        "prop_types",
        "predictors",
        "__backup",
        "__save_id",
        "__notifier",
        "__id_to_video",
        "__cache",
        "__quality_attribute",
        "__moves_attribute",
    )

    def __init__(
        self,
        path: PathType,
        folders: Optional[Iterable[PathType]] = None,
        notifier: Notifier = DEFAULT_NOTIFIER,
    ):
        self.settings = DbSettings()
        self.date = DateModified.now()
        self.folders: Set[AbsolutePath] = set()
        self.videos: Dict[AbsolutePath, Video] = {}
        self.prop_types: Dict[str, PropType] = {}
        self.predictors: Dict[str, List[float]] = {}
        self.__backup = JsonBackup(path)
        self.__notifier = notifier
        self.__save_id = 0
        self.__id_to_video: Dict[int, Video] = {}
        self.__cache = DbCache(self)
        self.__quality_attribute = QualityAttribute(self)
        self.__moves_attribute = PotentialMoveAttribute(self)
        self.__load(folders)

    iteration = property(lambda self: self.__save_id)
    quality_attribute = property(lambda self: self.__quality_attribute)
    moves_attribute = property(lambda self: self.__moves_attribute)
    id_to_video = property(lambda self: self.__id_to_video)
    notifier = property(lambda self: self.__notifier)

    @Profiler.profile_method()
    def __load(self, folders: Optional[Iterable[PathType]] = None):
        to_save = False

        json_dict = self.__backup.load()
        if not isinstance(json_dict, dict):
            raise exceptions.InvalidDatabaseJSON(self.__backup.path)

        # Parsing settings.
        self.settings.update(json_dict.get("settings", {}))

        # Parsing date.
        if "date" in json_dict:
            self.date = DateModified(json_dict["date"])

        # Parsing folders.
        self.folders.update(AbsolutePath(path) for path in json_dict.get("folders", ()))
        if folders:
            lb = len(self.folders)
            self.folders.update(AbsolutePath.ensure(path) for path in folders)
            to_save = to_save or lb != len(self.folders)

        # Parsing video property types.
        for prop_dict in json_dict.get("prop_types", ()):
            self.add_prop_type(PropType.from_dict(prop_dict), save=False)

        # Parsing predictors
        self.predictors = json_dict.get("predictors", {})

        # Parsing videos.
        folders_tree = PathTree(self.folders)
        for video_dict in json_dict.get("videos", ()):
            video_state = Video.from_dict(video_dict, database=self)
            video_state.discarded = not folders_tree.in_folders(video_state.filename)
            self.videos[video_state.filename] = video_state

        self.save(on_new_identifiers=to_save)
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
        self.__backup.save(
            {
                "settings": self.settings.to_dict(),
                "date": self.date.time,
                "folders": sorted(folder.path for folder in self.folders),
                "prop_types": [prop.to_dict() for prop in self.prop_types.values()],
                "predictors": self.predictors,
                "videos": sorted(
                    (video.to_dict() for video in self.videos.values()),
                    key=lambda dct: dct["f"],
                ),
            }
        )
        self.__notifier.notify(notifications.DatabaseSaved(self))

    def __ensure_identifiers(self):
        id_to_video = {}  # type: Dict[int, Video]
        without_identifiers = []
        for video_state in self.videos.values():
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

    def add_prop_type(self, prop: PropType, save: bool = True) -> None:
        if prop.name in self.prop_types:
            raise exceptions.PropertyAlreadyExists(prop.name)
        self.prop_types[prop.name] = prop
        if save:
            self.save()

    def set_path(self, path: PathType):
        self.__backup = JsonBackup(path)

    def query(self, required: Dict[str, bool] = None) -> List[Video]:
        videos = self.videos.values()
        return (
            [
                video
                for video in videos
                if all(getattr(video, flag) is required[flag] for flag in required)
            ]
            if required
            else list(videos)
        )

    def get_videos(self, *flags, **forced_flags) -> List[Video]:
        return self.__cache.get(*flags, **forced_flags)

    def get_prop_type(self, name: str) -> PropType:
        return self.prop_types[name]

    def get_prop_types(self) -> Iterable[PropType]:
        return self.prop_types.values()
