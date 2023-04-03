import logging
from typing import Any, Container, Dict, Iterable, List, Optional, Sequence, Set, Union

from pysaurus.application import exceptions
from pysaurus.core import functions, notifications, notifying
from pysaurus.core.components import AbsolutePath, Date, PathType
from pysaurus.core.json_backup import JsonBackup
from pysaurus.core.notifications import Notification
from pysaurus.core.notifying import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database.db_settings import DbSettings
from pysaurus.database.db_video_attribute import (
    PotentialMoveAttribute,
    QualityAttribute,
)
from pysaurus.database.special_properties import SpecialProperties
from pysaurus.properties.properties import (
    DefType,
    PROP_UNIT_TYPES,
    PROP_UNIT_TYPE_MAP,
    PropType,
    PropValueType,
)
from pysaurus.video import Video, VideoRuntimeInfo
from pysaurus.video.abstract_video_indexer import AbstractVideoIndexer
from pysaurus.video.video_features import VideoFeatures
from pysaurus.video.video_indexer import VideoIndexer
from pysaurus.video.video_sorting import VideoSorting

logger = logging.getLogger(__name__)


class DatabaseLoaded(Notification):
    __slots__ = (
        "entries",
        "discarded",
        "unreadable_not_found",
        "unreadable_found",
        "readable_not_found",
        "valid",
        "readable_found_without_thumbnails",
    )

    def __init__(self, database):
        super().__init__()
        self.entries = database.count_videos()
        self.discarded = database.count_videos("discarded")
        self.unreadable_not_found = database.count_videos("unreadable", "not_found")
        self.unreadable_found = database.count_videos("unreadable", "found")
        self.readable_not_found = database.count_videos("readable", "not_found")
        self.readable_found_without_thumbnails = database.count_videos(
            "readable", "found", "without_thumbnails"
        )
        self.valid = database.count_videos("readable", "found", "with_thumbnails")


class DatabaseSaved(DatabaseLoaded):
    __slots__ = ()


class _ToSave:
    __slots__ = "database", "to_save"

    def __init__(self, database, to_save=True):
        self.database = database
        self.to_save = to_save

    def __enter__(self):
        self.database.in_save_context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.database.in_save_context = False
        if self.to_save:
            self.database.save()
            logger.info("Saved in context.")


class JsonDatabase:
    __slots__ = (
        "__backup",
        "settings",
        "__date",
        "__folders",
        "__videos",
        "__prop_types",
        "__predictors",
        "iteration",
        "notifier",
        "__id_to_video",
        "quality_attribute",
        "moves_attribute",
        "__indexer",
        "in_save_context",
    )

    def __init__(
        self,
        path: PathType,
        folders: Optional[Iterable[PathType]] = None,
        notifier: Notifier = DEFAULT_NOTIFIER,
        indexer: AbstractVideoIndexer = None,
    ):
        # Private data
        self.__backup = JsonBackup(path)
        # Database content
        self.settings = DbSettings()
        self.__date = Date.now()
        self.__folders: Set[AbsolutePath] = set()
        self.__videos: Dict[AbsolutePath, Video] = {}
        self.__prop_types: Dict[str, PropType] = {}
        self.__predictors: Dict[str, List[float]] = {}
        # Runtime
        self.notifier = notifier
        self.iteration = 0
        self.__id_to_video: Dict[int, Video] = {}
        self.quality_attribute = QualityAttribute(self)
        self.moves_attribute = PotentialMoveAttribute(self)
        self.__indexer = indexer or VideoIndexer()
        self.in_save_context = False
        # Initialize
        self.__load(folders)

    date = property(lambda self: self.__date)
    video_folders = property(lambda self: list(self.__folders))

    @Profiler.profile_method()
    def __load(self, folders: Optional[Iterable[PathType]] = None):
        to_save = False

        with Profiler("loading JSON file", self.notifier):
            # Loading JSON file
            json_dict = self.__backup.load()
            if not isinstance(json_dict, dict):
                raise exceptions.InvalidDatabaseJSON(self.__backup.path)

        # Parsing settings.
        self.settings = DbSettings(json_dict.get("settings", {}))

        # Parsing date.
        if "date" in json_dict:
            self.__date = Date(json_dict["date"])

        # Parsing folders.
        self.__folders.update(
            AbsolutePath(path) for path in json_dict.get("folders", ())
        )
        if folders:
            lb = len(self.__folders)
            self.__folders.update(AbsolutePath.ensure(path) for path in folders)
            to_save = to_save or lb != len(self.__folders)

        # Parsing video property types.
        for prop_dict in json_dict.get("prop_types", ()):
            prop_type = PropType.from_dict(prop_dict)
            assert prop_type.name not in self.__prop_types
            self.__prop_types[prop_type.name] = prop_type

        # Parsing predictors
        self.__predictors = {
            name: predictor
            for name, predictor in json_dict.get("predictors", {}).items()
            if name in self.__prop_types
        }

        # Parsing videos.
        with Profiler("parsing videos", self.notifier):
            folders_tree = PathTree(self.__folders)
            for video_dict in json_dict.get("videos", ()):
                video_state = Video.from_dict(video_dict, database=self)
                video_state.discarded = not folders_tree.in_folders(
                    video_state.filename
                )
                self.__videos[video_state.filename] = video_state

        notifying.with_handler(
            self.notifier, self.__indexer.build, self.__videos.values()
        )
        self.save(on_new_identifiers=to_save)
        self.notifier.notify(DatabaseLoaded(self))

    @Profiler.profile_method()
    def __ensure_identifiers(self):
        id_to_video = {}  # type: Dict[int, Video]
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
        if without_identifiers:
            logger.debug(f"Generating {len(without_identifiers)} new video indices.")
        return len(without_identifiers)

    @Profiler.profile_method()
    def save(self, on_new_identifiers=False):
        """Save database on disk.

        Parameters
        ----------
        on_new_identifiers:
            if True, save only if new video IDs were generated.
        """
        identifiers_updated = self.__ensure_identifiers()
        if self.in_save_context:
            logger.info("Saving deactivated in context.")
            return
        logger.info("Saving.")
        if not identifiers_updated and on_new_identifiers:
            return
        self.iteration += 1
        # Save database.
        self.__backup.save(
            {
                "settings": self.settings.to_dict(),
                "date": self.date.time,
                "folders": [folder.path for folder in self.__folders],
                "prop_types": [prop.to_dict() for prop in self.__prop_types.values()],
                "predictors": self.__predictors,
                "videos": [video.to_dict() for video in self.__videos.values()],
            }
        )
        self.notifier.notify(DatabaseSaved(self))

    def to_save(self, to_save=True):
        return _ToSave(self, to_save=to_save)

    def set_path(self, path: PathType):
        self.__backup = JsonBackup(path)

    def set_date(self, date: Date):
        self.__date = date

    def set_folders(self, folders) -> None:
        folders = sorted(AbsolutePath.ensure(folder) for folder in folders)
        if folders == sorted(self.__folders):
            return
        folders_tree = PathTree(folders)
        for video in self.__videos.values():
            video.discarded = not folders_tree.in_folders(video.filename)
        self.__folders = set(folders)
        self.save()

    def get_predictor(self, prop_name):
        return self.__predictors.get(prop_name, None)

    def set_predictor(self, prop_name: str, theta: List[float]):
        self.__predictors[prop_name] = theta
        self.save()

    def get_cached_videos(self, *flags, **forced_flags):
        return [
            self.__videos[filename]
            for filename in self.__indexer.query_flags(
                self.__videos, *flags, **forced_flags
            )
        ]

    def count_videos(self, *flags, **forced_flags) -> int:
        if not flags and not forced_flags:
            return len(self.__videos)
        else:
            return len(self.get_cached_videos(*flags, **forced_flags))

    def select_videos_fields(
        self, fields: Sequence[str], *flags, **forced_flags
    ) -> Iterable[Dict[str, Any]]:
        return (
            {field: getattr(video, field) for field in fields}
            for video in self.get_cached_videos(*flags, **forced_flags)
        )

    def query(self, required: Dict[str, bool] = None) -> List[Video]:
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

    def sort_video_indices(self, indices: Iterable[int], sorting: VideoSorting):
        return sorted(
            indices,
            key=lambda video_id: self.__id_to_video[video_id].to_comparable(sorting),
        )

    def search(
        self, text: str, cond: str = "and", videos: Sequence[Video] = None
    ) -> Iterable[Video]:
        if not text:
            output = ()
        else:
            if videos is None:
                filenames: Dict[AbsolutePath, Video] = self.__videos
            else:
                filenames: Dict[AbsolutePath, Video] = {
                    video.filename: video for video in videos
                }
            terms = functions.string_to_pieces(text)
            if cond == "exact":
                with Profiler(f"query exact: {text}", self.notifier):
                    selection = (
                        filename
                        for filename in self.__indexer.query_and(filenames, terms)
                        if self.__videos[filename].has_exact_text(text)
                    )
            elif cond == "and":
                selection = self.__indexer.query_and(filenames, terms)
            elif cond == "or":
                selection = self.__indexer.query_or(filenames, terms)
            else:
                assert cond == "id"
                (term,) = terms
                video_id = int(term)
                selection = (
                    [self.__id_to_video[video_id].filename]
                    if video_id in self.__id_to_video
                    else []
                )
            output = (filenames[filename] for filename in selection)
        return output

    def has_prop_type(
        self, name, *, with_type=None, multiple=None, with_enum=None, default=None
    ) -> bool:
        if name not in self.__prop_types:
            return False
        pt = self.__prop_types[name]
        if with_type is not None and pt.type is not with_type:
            return False
        if multiple is not None and pt.multiple is not multiple:
            return False
        if with_enum is not None and not pt.is_enum(with_enum):
            return False
        if default is not None and pt.default != default:
            return False
        return True

    def describe_prop_types(self) -> List[dict]:
        return sorted(
            (prop.describe() for prop in self.__prop_types.values()),
            key=lambda d: d["name"],
        )

    def add_prop_type(self, prop: PropType) -> None:
        if prop.name in self.__prop_types:
            raise exceptions.PropertyAlreadyExists(prop.name)
        self.__prop_types[prop.name] = prop
        self.save()

    def create_prop_type(
        self,
        name: str,
        prop_type: Union[str, type],
        definition: DefType,
        multiple: bool,
    ) -> None:
        if isinstance(prop_type, str):
            prop_type = PROP_UNIT_TYPE_MAP[prop_type]
        assert prop_type in PROP_UNIT_TYPES
        if prop_type is float:
            if isinstance(definition, (list, tuple)):
                definition = [float(element) for element in definition]
            else:
                definition = float(definition)
        self.add_prop_type(PropType(name, definition, multiple))

    def remove_prop_type(self, name) -> None:
        if name in self.__prop_types:
            del self.__prop_types[name]
            for video in self.__videos.values():
                video.remove_property(name, None)
            self.save()

    def rename_prop_type(self, old_name, new_name) -> None:
        if self.has_prop_type(old_name):
            if self.has_prop_type(new_name):
                raise exceptions.PropertyAlreadyExists(new_name)
            prop_type = self.__prop_types.pop(old_name)
            prop_type.name = new_name
            self.__prop_types[new_name] = prop_type
            for video in self.__videos.values():
                if video.has_property(old_name):
                    video.set_property(new_name, video.remove_property(old_name))
            self.save()

    def convert_prop_to_unique(self, name) -> None:
        if self.has_prop_type(name):
            prop_type = self.__prop_types[name]
            if not prop_type.multiple:
                raise exceptions.PropertyAlreadyUnique(name)
            for video in self.__videos.values():
                if video.has_property(name) and len(video.get_property(name)) > 1:
                    raise exceptions.PropertyToUniqueError(name, video)
            prop_type.multiple = False
            for video in self.__videos.values():
                if video.has_property(name):
                    if video.get_property(name):
                        video.set_property(name, video.get_property(name)[0])
                    else:
                        # delete property value
                        video.remove_property(name)
            self.save()

    def convert_prop_to_multiple(self, name) -> None:
        if self.has_prop_type(name):
            prop_type = self.__prop_types[name]
            if prop_type.multiple:
                raise exceptions.PropertyAlreadyMultiple(name)
            prop_type.multiple = True
            for video in self.__videos.values():
                if video.has_property(name):
                    video.set_property(name, [video.get_property(name)])
            self.save()

    def get_prop_values(
        self, video_id: int, name: str, default=False
    ) -> List[PropValueType]:
        video = self.__id_to_video[video_id]
        values = []
        if video.has_property(name):
            value = video.get_property(name)
            values = value if self.__prop_types[name].multiple else [value]
        assert isinstance(values, list)
        if default and not values and not self.__prop_types[name].multiple:
            values = [self.__prop_types[name].default]
        return values

    def set_prop_values(
        self, video_id: int, name: str, values: Union[Sequence, Set]
    ) -> None:
        video = self.__id_to_video[video_id]
        if not values:
            video.remove_property(name, None)
        elif self.__prop_types[name].multiple:
            video.set_property(name, self.__prop_types[name].validate(values))
        else:
            (value,) = values
            video.set_property(name, self.__prop_types[name].validate(value))

    def set_video_properties(self, video_id: int, properties: dict) -> Set[str]:
        video = self.__id_to_video[video_id]
        modified = video.set_validated_properties(properties)
        self._notify_properties_modified(modified, [video_id])
        return modified

    def merge_prop_values(
        self, video_id: int, name: str, values: Union[Sequence, Set]
    ) -> None:
        video = self.__id_to_video[video_id]
        if self.__prop_types[name].multiple:
            values = video.get_property(name, []) + list(values)
        self.set_prop_values(video.video_id, name, values)

    def validate_prop_values(self, name, values: list) -> List[PropValueType]:
        prop_type = self.__prop_types[name]
        if prop_type.multiple:
            values = prop_type.validate(values)
        else:
            values = [prop_type.validate(value) for value in values]
        return values

    def new_prop_val(self, name, value=None) -> PropValueType:
        pt = self.__prop_types[name]
        return pt.default if value is None else pt.validate(value)

    def _update_videos_not_found(self, existing_paths: Container[AbsolutePath]):
        """Use given container of existing paths to mark not found videos."""
        modified = []
        for video_state in self.__videos.values():
            is_file = video_state.filename in existing_paths
            if video_state.runtime.is_file is not is_file:
                video_state.runtime.is_file = is_file
                modified.append(video_state)
        if modified:
            self.__indexer.update_videos(modified)

    def _notify_properties_modified(self, properties, video_indices: Iterable[int]):
        self.save()
        self.__indexer.update_videos(
            (self.__id_to_video[video_id] for video_id in video_indices)
        )
        self.notifier.notify(notifications.PropertiesModified(properties))

    def _notify_fields_modified(self, fields: Sequence[str]):
        self.save()
        self.notifier.notify(notifications.FieldsModified(fields))

    def _notify_filename_modified(self, video: Video, old_path: AbsolutePath):
        self._notify_fields_modified(
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
        self.__indexer.replace_path(video, old_path)

    def _notify_missing_thumbnails(self, modified: Iterable[int] = ()):
        self.__indexer.update_videos(
            self.__id_to_video[video_id] for video_id in modified
        )
        remaining_thumb_videos = [
            video.filename.path
            for video in self.get_cached_videos(
                "readable", "found", "without_thumbnails"
            )
        ]
        self.notifier.notify(notifications.MissingThumbnails(remaining_thumb_videos))
        self.save()

    def _find_video_paths_for_update(
        self, file_paths: Dict[AbsolutePath, VideoRuntimeInfo]
    ) -> List[str]:
        all_file_names = []
        for file_name, file_info in file_paths.items():
            video: Video = self.__videos.get(file_name, None)
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

    def get_all_video_indices(self) -> Iterable[int]:
        return self.__id_to_video.keys()

    def has_video(self, filename: AbsolutePath) -> bool:
        return filename in self.__videos

    def has_video_id(self, video_id: int) -> bool:
        return video_id in self.__id_to_video

    def get_video_filename(self, video_id: int) -> AbsolutePath:
        return self.__id_to_video[video_id].filename

    def get_video_id(self, filename: PathType):
        filename = AbsolutePath.ensure(filename)
        if filename in self.__videos:
            return self.__videos[filename].video_id
        else:
            return None

    def get_video_terms(self, video_id: int) -> Set[str]:
        return self.__id_to_video[video_id].terms(as_set=True)

    def read_video_field(self, video_id: int, field: str):
        return getattr(self.__id_to_video[video_id], field)

    def read_video_fields(self, video_id: int, fields: Sequence[str]) -> dict:
        video = self.__id_to_video[video_id]
        return {field: getattr(video, field) for field in fields}

    def read_videos_field(self, indices: Iterable[int], field: str) -> Iterable:
        return (getattr(self.__id_to_video[video_id], field) for video_id in indices)

    def write_video_field(self, video_id: int, field: str, value, notify=False) -> bool:
        video = self.__id_to_video[video_id]
        previous_value = getattr(video, field)
        modified = previous_value != value
        if modified:
            setattr(video, field, value)
            if notify:
                with self.to_save(False):
                    self._notify_fields_modified([field])
        return modified

    def write_video_fields(self, video_id: int, **kwargs) -> bool:
        modified = False
        video = self.__id_to_video[video_id]
        for key, value in kwargs.items():
            previous_value = getattr(video, key)
            if previous_value != value:
                setattr(video, key, value)
                modified = True
        return modified

    def write_videos_field(self, indices: Iterable[int], field: str, values: Iterable):
        for video_id, value in zip(indices, values):
            setattr(self.__id_to_video[video_id], field, value)

    def write_new_videos(
        self,
        dictionaries: List[dict],
        runtime_info: Dict[AbsolutePath, VideoRuntimeInfo],
    ) -> None:
        videos: List[Video] = []
        unreadable: List[Video] = []
        for d in dictionaries:
            file_path = AbsolutePath.ensure(d["f"])
            if len(d) == 2:
                video_state = Video.from_keys(
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
                if self.has_video(file_path) and self.read_video_field(
                    self.get_video_id(file_path), "readable"
                ):
                    old_video = self.__videos[file_path]
                    video_state.set_properties(old_video.properties)
                    video_state.similarity_id = old_video.similarity_id
                    video_state.video_id = old_video.video_id
                # Set special properties
                SpecialProperties.set(video_state)
            video_state.runtime = runtime_info[file_path]
            videos.append(video_state)
        self.__videos.update({video.filename: video for video in videos})
        self.__indexer.update_videos(videos)
        if unreadable:
            self.notifier.notify(
                notifications.VideoInfoErrors(
                    {
                        video_state.filename: video_state.errors
                        for video_state in unreadable
                    }
                )
            )
        self.save()

    def fill_videos_field(self, indices: Iterable[int], field: str, value):
        for video_id in indices:
            setattr(self.__id_to_video[video_id], field, value)

    def change_video_path(self, video_id: int, path: AbsolutePath) -> AbsolutePath:
        path = AbsolutePath.ensure(path)
        assert path.isfile()
        video = self.__id_to_video[video_id]
        assert video.readable
        assert video.filename != path
        old_filename = video.filename

        del self.__videos[video.filename]
        self.__videos[path] = video
        # TODO video.filename should be immutable
        # We should instead copy video object with a new filename
        video.filename = path
        self._notify_filename_modified(video, old_filename)

        return old_filename

    def delete_video_entry(self, video_id: int):
        video = self.__id_to_video[video_id]
        self.__videos.pop(video.filename, None)
        self.__id_to_video.pop(video.video_id, None)
        if video.readable:
            video.thumbnail_path.delete()
        self.__indexer.remove_video(video)
        self.notifier.notify(notifications.VideoDeleted(video))
        self._notify_fields_modified(["move_id", "quality"])

    def move_video_entry(self, from_id, to_id):
        from_video = self.__id_to_video[from_id]
        to_video = self.__id_to_video[to_id]
        assert not from_video.found
        assert to_video.found
        for prop_name in self.__prop_types.keys():
            self.merge_prop_values(
                to_id, prop_name, self.get_prop_values(from_id, prop_name)
            )
        to_video.similarity_id = from_video.similarity_id
        to_video.date_entry_modified = from_video.date_entry_modified.time
        to_video.date_entry_opened = from_video.date_entry_opened.time
        self.__indexer.update_videos([to_video])
        self.delete_video_entry(from_id)

    def open_video(self, video_id: int):
        self.__id_to_video[video_id].open()
        self._notify_fields_modified(["date_entry_opened"])

    @Profiler.profile_method()
    def describe_videos(self, video_indices: Sequence[int]):
        return [
            VideoFeatures.json(self.__id_to_video[video_id])
            for video_id in video_indices
        ]

    @Profiler.profile_method()
    def get_common_fields(self, video_indices: Iterable[int]) -> dict:
        return VideoFeatures.get_common_fields(
            self.__id_to_video[video_id] for video_id in video_indices
        )
