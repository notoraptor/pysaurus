import logging
from typing import Any, Container, Dict, Iterable, List, Optional, Sequence, Set, Union

from pysaurus.application import exceptions
from pysaurus.core import functions, notifications, notifying
from pysaurus.core.components import AbsolutePath, Date, PathType
from pysaurus.core.json_backup import JsonBackup
from pysaurus.core.notifying import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database.db_paths import DatabasePathDef, DatabasePaths
from pysaurus.database.db_settings import DbSettings
from pysaurus.database.db_video_attribute import PotentialMoveAttribute
from pysaurus.database.json_database_utils import (
    DatabaseLoaded,
    DatabaseSaved,
    DatabaseToSaveContext,
    patch_database_json,
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

DB_JSON_PATH = DatabasePathDef("json_path", "json")
DB_LOG_PATH = DatabasePathDef("log_path", "log")
DB_THUMB_FOLDER = DatabasePathDef("thumb_folder", "thumbnails")
DB_MINIATURES_PATH = DatabasePathDef("miniatures_path", "miniatures.json")
DB_INDEX_SQL_PATH = DatabasePathDef("index_sql_path", "db")
DB_INDEX_PKL_PATH = DatabasePathDef("index_pkl_path", "index.pkl")


class JsonDatabase:
    __slots__ = (
        "ways",
        "__backup",
        "__version",
        "settings",
        "__date",
        "__folders",
        "__videos",
        "__prop_types",
        "__predictors",
        "iteration",
        "notifier",
        "__id_to_video",
        "moves_attribute",
        "__indexer",
        "in_save_context",
        "__removed",
        "__modified",
    )

    def __init__(
        self,
        db_folder: PathType,
        folders: Optional[Iterable[PathType]] = None,
        notifier: Notifier = DEFAULT_NOTIFIER,
        indexer: AbstractVideoIndexer = None,
    ):
        db_folder = AbsolutePath.ensure_directory(db_folder)
        self.ways = DatabasePaths(db_folder)
        self.ways.define(DB_JSON_PATH)
        self.ways.define(DB_LOG_PATH)
        self.ways.define(DB_THUMB_FOLDER, True, True)
        self.ways.define(DB_MINIATURES_PATH)
        self.ways.define(DB_INDEX_SQL_PATH)
        self.ways.define(DB_INDEX_PKL_PATH)
        # Set log file
        notifier.set_log_path(self.ways.get(DB_LOG_PATH).path)
        # Private data
        self.__backup = JsonBackup(self.ways.get(DB_JSON_PATH), notifier)
        # Database content
        self.__version = 0
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
        self.moves_attribute = PotentialMoveAttribute(self)
        self.__indexer = indexer or VideoIndexer(
            self.notifier, self.ways.get(DB_INDEX_PKL_PATH)
        )
        self.in_save_context = False
        self.__removed: Set[Video] = set()
        self.__modified: Set[Video] = set()
        # Initialize
        self.__load(folders)

    @Profiler.profile_method()
    def __load(self, folders: Optional[Iterable[PathType]] = None):
        to_save = False

        with Profiler("loading JSON file", self.notifier):
            # Loading JSON file
            json_dict = self.__backup.load()
            if not isinstance(json_dict, dict):
                raise exceptions.InvalidDatabaseJSON(self.__backup.path)

        # Parsing version.
        version = json_dict.get("version", -1)
        assert version <= self.__version
        if version < self.__version:
            with Profiler("patch", self.notifier):
                patch_database_json(json_dict, version)
            to_save = True

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
            self.__videos = {
                video_state.filename: video_state
                for video_state in (
                    Video(
                        short_dict=video_dict,
                        database=self,
                        discarded=not folders_tree.in_folders(
                            AbsolutePath(video_dict["f"])
                        ),
                    )
                    for video_dict in json_dict.get("videos", ())
                )
            }

        # Build indexer
        notifying.with_handler(
            self.notifier, self.__indexer.build, self.__videos.values()
        )

        # Finish loading
        self.save(on_new_identifiers=not to_save)
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
        # Update identifiers anyway
        identifiers_updated = self.__ensure_identifiers()
        # Do not save if in save context
        if self.in_save_context:
            logger.info("Saving deactivated in context.")
            return
        # Do not save if we must save only on new identifiers.
        if not identifiers_updated and on_new_identifiers:
            return
        # We can save. Make runtime updates.
        self.iteration += 1
        # Save database.
        self.__backup.save(
            {
                "version": self.__version,
                "settings": self.settings.to_dict(),
                "date": self.__date.time,
                "folders": [folder.path for folder in self.__folders],
                "prop_types": [prop.to_dict() for prop in self.__prop_types.values()],
                "predictors": self.__predictors,
                "videos": [video.to_dict() for video in self.__videos.values()],
            }
        )
        self.notifier.notify(DatabaseSaved(self))

    def __close__(self):
        """Close database."""
        self.__indexer.close()

    def to_save(self, to_save=True):
        return DatabaseToSaveContext(self, to_save=to_save)

    def register_modified(self, video: Video):
        if video in self.__removed:
            self.__removed.remove(video)
        self.__modified.add(video)

    def register_removed(self, video: Video):
        if video in self.__modified:
            self.__modified.remove(video)
        self.__removed.add(video)

    def register_replaced(self, new_video: Video, old_video: Video):
        self.register_removed(old_video)
        self.register_modified(new_video)

    def flush_changes(self):
        # Prepare updating moves_attribute if having removed or added videos.
        nb_added = len(self.__modified) - len(
            self.__indexer.indexed_videos(self.__modified)
        )
        self.moves_attribute.force_update = bool(
            self.moves_attribute.force_update or self.__removed or nb_added
        )

        if self.__removed:
            logger.info(f"Flushed {len(self.__removed)} removed")
            self.__indexer.remove_videos(self.__removed)
        if self.__modified:
            logger.info(f"Flushed {len(self.__modified)} modified")
            self.__indexer.update_videos(self.__modified)
        self.__removed.clear()
        self.__modified.clear()

    def rename(self, new_name: str) -> None:
        self.ways = self.ways.renamed(new_name)
        self.notifier.set_log_path(self.ways.get(DB_LOG_PATH).path)
        self.__backup = JsonBackup(self.ways.get(DB_JSON_PATH), self.notifier)

    def set_date(self, date: Date):
        self.__date = date

    def get_date(self) -> Date:
        return self.__date

    def set_folders(self, folders) -> None:
        folders = sorted(AbsolutePath.ensure(folder) for folder in folders)
        if folders == sorted(self.__folders):
            return
        folders_tree = PathTree(folders)
        for video in self.__videos.values():
            video.discarded = not folders_tree.in_folders(video.filename)
        self.__folders = set(folders)
        self.save()

    def get_folders(self) -> Iterable[AbsolutePath]:
        return iter(self.__folders)

    def set_predictor(self, prop_name: str, theta: List[float]):
        self.__predictors[prop_name] = theta
        self.save()

    def get_predictor(self, prop_name):
        return self.__predictors.get(prop_name, None)

    def _get_cached_videos(self, *flags, **forced_flags) -> List[Video]:
        if flags or forced_flags:
            self.flush_changes()
            return [
                self.__videos[filename]
                for filename in self.__indexer.query_flags(
                    self.__videos, *flags, **forced_flags
                )
            ]
        else:
            return list(self.__videos.values())

    def count_videos(self, *flags, **forced_flags) -> int:
        if not flags and not forced_flags:
            return len(self.__videos)
        else:
            return len(self._get_cached_videos(*flags, **forced_flags))

    def select_videos_fields(
        self, fields: Sequence[str], *flags, **forced_flags
    ) -> Iterable[Dict[str, Any]]:
        return (
            {field: getattr(video, field) for field in fields}
            for video in self._get_cached_videos(*flags, **forced_flags)
        )

    def search_flags(self, *flags, **forced_flags) -> List[int]:
        return [
            video.video_id for video in self._get_cached_videos(*flags, **forced_flags)
        ]

    def search(
        self, text: str, cond: str = "and", videos: Sequence[int] = None
    ) -> Iterable[Video]:
        if not text:
            output = ()
        else:
            self.flush_changes()
            if videos is None:
                filenames: Dict[AbsolutePath, Video] = self.__videos
            else:
                filenames: Dict[AbsolutePath, Video] = {
                    self.__id_to_video[video_id].filename: self.__id_to_video[video_id]
                    for video_id in videos
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

    def sort_video_indices(self, indices: Iterable[int], sorting: VideoSorting):
        return sorted(
            indices,
            key=lambda video_id: self.__id_to_video[video_id].to_comparable(sorting),
        )

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

    def get_string_properties(self) -> List[str]:
        return [pt.name for pt in self.__prop_types.values() if pt.type is str]

    def describe_prop_types(self) -> List[dict]:
        return sorted(
            (prop.describe() for prop in self.__prop_types.values()),
            key=lambda d: d["name"],
        )

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
        prop = PropType(name, definition, multiple)
        assert prop.type is prop_type
        if prop.name in self.__prop_types:
            raise exceptions.PropertyAlreadyExists(prop.name)
        self.__prop_types[prop.name] = prop
        self.save()

    def remove_prop_type(self, name) -> None:
        if name in self.__prop_types:
            del self.__prop_types[name]
            for video in self.__videos.values():
                video.remove_property(name)
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
                if video.has_property(name) and len(video.get_property(name)) != 1:
                    raise exceptions.PropertyToUniqueError(
                        str(video.filename), name, video.get_property(name)
                    )
            prop_type.multiple = False
            # There should be nothing more to do.
            # For each video having this property,
            # there should already be a list with exactly 1 value.
            self.save()

    def convert_prop_to_multiple(self, name) -> None:
        if self.has_prop_type(name):
            prop_type = self.__prop_types[name]
            if prop_type.multiple:
                raise exceptions.PropertyAlreadyMultiple(name)
            prop_type.multiple = True
            # There should be nothing more to do.
            # Property value should already be a list
            # for videos having this property.
            self.save()

    def get_prop_values(self, video_id: int, name: str) -> List[PropValueType]:
        return self.__id_to_video[video_id].get_property(name)

    def set_prop_values(
        self, video_id: int, name: str, values: Union[Sequence, Set]
    ) -> None:
        video = self.__id_to_video[video_id]
        if not values:
            video.remove_property(name)
        elif self.__prop_types[name].multiple:
            video.set_property(name, self.__prop_types[name].validate(values))
        else:
            (value,) = values
            video.set_property(name, self.__prop_types[name].validate(value))

    def set_video_properties(self, video_id: int, properties: dict) -> List[str]:
        modified = self.__id_to_video[video_id].set_properties(
            {
                name: self.__prop_types[name].validate(value)
                for name, value in properties.items()
            }
        )
        self._notify_properties_modified(modified)
        return modified

    def merge_prop_values(
        self, video_id: int, name: str, values: Union[Sequence, Set]
    ) -> None:
        pt = self.__prop_types[name]
        if pt.multiple:
            values = pt.validate(
                self.__id_to_video[video_id].get_property(name) + list(values)
            )
        self.set_prop_values(video_id, name, values)

    def validate_prop_values(self, name, values: list) -> List[PropValueType]:
        prop_type = self.__prop_types[name]
        if prop_type.multiple:
            values = prop_type.validate(values)
        else:
            values = [prop_type.validate(value) for value in values]
        return values

    def default_prop_unit(self, name):
        pt = self.__prop_types[name]
        return None if pt.multiple else pt.default

    def value_is_default(self, name: str, value: list) -> bool:
        pt = self.__prop_types[name]
        return (not value) if pt.multiple else (value == [pt.default])

    def _update_videos_not_found(self, existing_paths: Container[AbsolutePath]):
        """Use given container of existing paths to mark not found videos."""
        for video_state in self.__videos.values():
            video_state.found = video_state.filename in existing_paths

    def _notify_properties_modified(self, properties):
        self.save()
        self.notifier.notify(notifications.PropertiesModified(properties))

    def _notify_fields_modified(self, fields: Sequence[str]):
        self.save()
        self.notifier.notify(notifications.FieldsModified(fields))

    def _notify_filename_modified(self, new_video: Video, old_video: Video):
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
        self.register_replaced(new_video, old_video)

    def _notify_missing_thumbnails(self):
        remaining_thumb_videos = [
            video.filename.path
            for video in self._get_cached_videos(
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
                or self._video_must_be_updated(video)
            ):
                all_file_names.append(file_name.path)
        all_file_names.sort()
        return all_file_names

    @classmethod
    def _video_must_be_updated(cls, video: Video):
        # A video readable with existing audio stream must have valid audio bits
        return video.readable and video.audio_codec and not video.audio_bits

    def get_all_video_indices(self) -> Iterable[int]:
        return self.__id_to_video.keys()

    def has_video(self, filename: AbsolutePath, **with_fields) -> bool:
        video = self.__videos.get(filename)
        return video and (
            not with_fields
            or all(getattr(video, key) == value for key, value in with_fields.items())
        )

    def has_video_id(self, video_id: int, **with_fields) -> bool:
        video = self.__id_to_video.get(video_id)
        return video and (
            not with_fields
            or all(getattr(video, key) == value for key, value in with_fields.items())
        )

    def get_video_filename(self, video_id: int) -> AbsolutePath:
        return self.__id_to_video[video_id].filename

    def get_video_id(self, filename: PathType):
        filename = AbsolutePath.ensure(filename)
        if filename in self.__videos:
            return self.__videos[filename].video_id
        else:
            return None

    def get_video_terms(self, video_id: int) -> List[str]:
        return self.__id_to_video[video_id].terms()

    def read_video_field(self, video_id: int, field: str):
        return getattr(self.__id_to_video[video_id], field)

    def read_video_fields(self, video_id: int, fields: Sequence[str]) -> dict:
        video = self.__id_to_video[video_id]
        return {field: getattr(video, field) for field in fields}

    def read_videos_field(self, indices: Iterable[int], field: str) -> Iterable:
        return (getattr(self.__id_to_video[video_id], field) for video_id in indices)

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
                    errors=sorted(d["e"]),
                    unreadable=True,
                    database=self,
                )
                unreadable.append(video_state)
            else:
                video_state = Video.from_dict(d, database=self)
                # Get previous properties, if available
                if self.has_video(file_path, readable=True):
                    old_video = self.__videos[file_path]
                    video_state.properties = old_video.properties
                    video_state.similarity_id = old_video.similarity_id
                    video_state.video_id = old_video.video_id
                    video_state.thumb_name = old_video.thumb_name
                    video_state.unreadable_thumbnail = old_video.unreadable_thumbnail
                    video_state.date_entry_opened = old_video.date_entry_opened.time
                # Set special properties
                SpecialProperties.set(video_state)
            # Video modified, so automatically added to __modified.
            video_state.runtime = runtime_info[file_path]
            videos.append(video_state)
        self.__videos.update({video.filename: video for video in videos})
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

    def fill_videos_field(self, indices: Iterable[int], field: str, value):
        for video_id in indices:
            setattr(self.__id_to_video[video_id], field, value)

    def change_video_entry_filename(
        self, video_id: int, path: AbsolutePath
    ) -> AbsolutePath:
        """Map video to new path in database.

        Return the previous path related to video.
        """
        path = AbsolutePath.ensure(path)
        assert path.isfile()
        video = self.__id_to_video[video_id]
        assert video.readable
        assert video.filename != path

        del self.__videos[video.filename]
        new_video = video.with_new_filename(path)
        self.__videos[new_video.filename] = new_video
        self._notify_filename_modified(new_video, video)

        return video.filename

    def delete_video_entry(self, video_id: int):
        video = self.__id_to_video[video_id]
        self.__videos.pop(video.filename, None)
        self.__id_to_video.pop(video.video_id, None)
        if video.readable:
            video.thumbnail_path.delete()
        self.register_removed(video)
        self.notifier.notify(notifications.VideoDeleted(video))
        self._notify_fields_modified(["move_id", "quality"])

    def move_video_entry(self, from_id, to_id) -> None:
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
        self.delete_video_entry(from_id)

    def open_video(self, video_id: int) -> None:
        self.__id_to_video[video_id].open()
        self._notify_fields_modified(["date_entry_opened"])

    @Profiler.profile_method()
    def describe_videos(self, video_indices: Sequence[int], with_moves=False):
        return [
            VideoFeatures.json(self.__id_to_video[video_id], with_moves)
            for video_id in video_indices
        ]

    @Profiler.profile_method()
    def get_common_fields(self, video_indices: Iterable[int]) -> dict:
        return VideoFeatures.get_common_fields(
            self.__id_to_video[video_id] for video_id in video_indices
        )
