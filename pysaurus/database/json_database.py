from typing import Dict, Iterable, List, Optional, Set, Sequence, Union

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
from pysaurus.database.properties import PropType, PropValueType
from pysaurus.database.video import Video


class JsonDatabase:
    __slots__ = (
        "__backup",
        "get_videos",
        "settings",
        "date",
        "folders",
        "videos",
        "prop_types",
        "predictors",
        "iteration",
        "notifier",
        "id_to_video",
        "quality_attribute",
        "moves_attribute",
    )

    def __init__(
        self,
        path: PathType,
        folders: Optional[Iterable[PathType]] = None,
        notifier: Notifier = DEFAULT_NOTIFIER,
    ):
        # Private data
        self.__backup = JsonBackup(path)
        self.get_videos = DbCache(self)
        # Database content
        self.settings = DbSettings()
        self.date = DateModified.now()
        self.folders: Set[AbsolutePath] = set()
        self.videos: Dict[AbsolutePath, Video] = {}
        self.prop_types: Dict[str, PropType] = {}
        self.predictors: Dict[str, List[float]] = {}
        # Runtime
        self.notifier = notifier
        self.iteration = 0
        self.id_to_video: Dict[int, Video] = {}
        self.quality_attribute = QualityAttribute(self)
        self.moves_attribute = PotentialMoveAttribute(self)
        # Initialize
        self.__load(folders)

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
        self.predictors = {
            name: predictor
            for name, predictor in json_dict.get("predictors", {}).items()
            if name in self.prop_types
        }

        # Parsing videos.
        folders_tree = PathTree(self.folders)
        for video_dict in json_dict.get("videos", ()):
            video_state = Video.from_dict(video_dict, database=self)
            video_state.discarded = not folders_tree.in_folders(video_state.filename)
            self.videos[video_state.filename] = video_state

        self.save(on_new_identifiers=to_save)
        self.notifier.notify(notifications.DatabaseLoaded(self))

    @Profiler.profile_method()
    def save(self, on_new_identifiers=False):
        """Save database on disk.

        :param on_new_identifiers: if True, save only if new video IDs were generated.
        """
        if not self.__ensure_identifiers() and on_new_identifiers:
            return
        self.iteration += 1
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
        self.notifier.notify(notifications.DatabaseSaved(self))

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
        self.id_to_video = id_to_video
        return len(without_identifiers)

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

    def _get_prop_types(self) -> Iterable[PropType]:
        return self.prop_types.values()

    def has_prop_type(
        self, name, *, with_type=None, multiple=None, with_enum=None, default=None
    ) -> bool:
        if name not in self.prop_types:
            return False
        pt = self.prop_types[name]
        if with_type is not None and pt.type is not with_type:
            return False
        if multiple is not None and pt.multiple is not multiple:
            return False
        if with_enum is not None and not pt.is_enum(with_enum):
            return False
        if default is not None and pt.default != default:
            return False
        return True

    def get_prop_val(self, name, value) -> PropValueType:
        return self.prop_types[name](value)

    def get_default_prop_val(self, name) -> PropValueType:
        return self.prop_types[name].default

    def get_prop_names(self) -> Iterable[str]:
        return self.prop_types.keys()

    def describe_prop_types(self) -> List[dict]:
        return sorted(
            (prop.describe() for prop in self.prop_types.values()),
            key=lambda d: d["name"],
        )

    def add_prop_type(self, prop: PropType, save: bool = True) -> None:
        if prop.name in self.prop_types:
            raise exceptions.PropertyAlreadyExists(prop.name)
        self.prop_types[prop.name] = prop
        if save:
            self.save()

    def remove_prop_type(self, name, save: bool = True) -> None:
        if name in self.prop_types:
            del self.prop_types[name]
            for video in self.query():
                video.remove_property(name)
            if save:
                self.save()

    def rename_prop_type(self, old_name, new_name) -> None:
        if self.has_prop_type(old_name):
            if self.has_prop_type(new_name):
                raise exceptions.PropertyAlreadyExists(new_name)
            prop_type = self.prop_types.pop(old_name)
            prop_type.name = new_name
            self.prop_types[new_name] = prop_type
            for video in self.query():
                if old_name in video.properties:
                    video.properties[new_name] = video.properties.pop(old_name)
            self.save()

    def convert_prop_to_unique(self, name) -> None:
        if self.has_prop_type(name):
            prop_type = self.prop_types[name]
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
            prop_type = self.prop_types[name]
            if prop_type.multiple:
                raise exceptions.PropertyAlreadyMultiple(name)
            prop_type.multiple = True
            for video in self.query():
                if name in video.properties:
                    video.properties[name] = [video.properties[name]]
            self.save()

    def get_prop_values(self, video: Video, name: str) -> list:
        values = []
        if name in video.properties:
            value = video.properties[name]
            values = value if self.prop_types[name].multiple else [value]
        assert isinstance(values, list)
        return values

    def set_prop_values(
        self, video: Video, name: str, values: Union[Sequence, Set]
    ) -> None:
        if not values:
            video.properties.pop(name, None)
        elif self.prop_types[name].multiple:
            video.properties[name] = self.prop_types[name].validate(values)
        else:
            (value,) = values
            video.properties[name] = self.prop_types[name].validate(value)

    def merge_prop_values(
        self, video: Video, name: str, values: Union[Sequence, Set]
    ) -> None:
        if self.prop_types[name].multiple:
            values = video.properties.get(name, []) + list(values)
        self.set_prop_values(video, name, values)

    def validate_prop_values(self, name, values: list) -> list:
        prop_type = self.prop_types[name]
        if prop_type.multiple:
            values = prop_type.validate(values)
        else:
            values = [prop_type.validate(value) for value in values]
        return values
