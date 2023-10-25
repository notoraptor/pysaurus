import logging
from abc import abstractmethod
from typing import Any, Container, Dict, Iterable, List, Optional, Sequence, Set, Union

from pysaurus.application import exceptions
from pysaurus.core import functions, notifications
from pysaurus.core.components import AbsolutePath, Date, PathType
from pysaurus.core.constants import JPEG_EXTENSION
from pysaurus.core.json_backup import JsonBackup
from pysaurus.core.notifying import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.db_settings import DbSettings
from pysaurus.database.db_video_attribute import PotentialMoveAttribute
from pysaurus.database.json_database_utils import (
    DatabaseLoaded,
    DatabaseSaved,
    DatabaseToSaveContext,
    patch_database_json,
)
from pysaurus.database.special_properties import SpecialProperties
from pysaurus.database.thubmnail_database.thumbnail_manager import ThumbnailManager
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
from saurus.sql.sql_old.video_entry import VideoEntry

logger = logging.getLogger(__name__)


class _ABJ(AbstractDatabase):
    __slots__ = ()

    @abstractmethod
    def __close__(self):
        """Close database."""
        raise NotImplementedError()

    @abstractmethod
    def to_save(self, to_save):
        raise NotImplementedError()

    @abstractmethod
    def set_predictor(self, prop_name, theta):
        raise NotImplementedError()

    @abstractmethod
    def get_predictor(self, prop_name):
        raise NotImplementedError()

    @abstractmethod
    def count_videos(self, flags, forced_flags):
        raise NotImplementedError()

    @abstractmethod
    def has_prop_type(self, name, with_type, multiple, with_enum, default):
        raise NotImplementedError()

    @abstractmethod
    def describe_prop_types(self):
        raise NotImplementedError()

    @abstractmethod
    def create_prop_type(self, name, prop_type, definition, multiple):
        raise NotImplementedError()

    @abstractmethod
    def remove_prop_type(self, name):
        raise NotImplementedError()

    @abstractmethod
    def rename_prop_type(self, old_name, new_name):
        raise NotImplementedError()

    @abstractmethod
    def convert_prop_to_unique(self, name):
        raise NotImplementedError()

    @abstractmethod
    def convert_prop_to_multiple(self, name):
        raise NotImplementedError()

    @abstractmethod
    def get_prop_values(self, video_id, name):
        raise NotImplementedError()

    @abstractmethod
    def set_prop_values(self, video_id, name, values):
        raise NotImplementedError()

    @abstractmethod
    def merge_prop_values(self, video_id, name, values):
        raise NotImplementedError()

    @abstractmethod
    def validate_prop_values(self, name, values):
        raise NotImplementedError()

    @abstractmethod
    def set_video_properties(self, video_id, properties):
        raise NotImplementedError()

    @abstractmethod
    def value_is_default(self, name, value):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def _video_must_be_updated(cls, video):
        raise NotImplementedError()

    @abstractmethod
    def get_all_video_indices(self):
        raise NotImplementedError()

    @abstractmethod
    def get_video_terms(self, video_id):
        raise NotImplementedError()

    @abstractmethod
    def move_video_entry(self, from_id, to_id):
        raise NotImplementedError()

    @abstractmethod
    def confirm_unique_moves(self):
        raise NotImplementedError()

    @abstractmethod
    def open_video(self, video_id):
        raise NotImplementedError()

    @abstractmethod
    def describe_videos(self, video_indices, with_moves):
        raise NotImplementedError()

    @abstractmethod
    def get_common_fields(self, video_indices):
        raise NotImplementedError()


class _JsonDatabase(_ABJ):
    __slots__ = (
        "_version",
        "settings",
        "_date",
        "_folders",
        "_videos",
        "_prop_types",
        "_predictors",
        "_id_to_video",
        "moves_attribute",
        "_indexer",
        "in_save_context",
        "_removed",
        "_modified",
        "_thumb_mgr",
    )

    def __init__(
        self,
        db_folder: PathType,
        folders: Optional[Iterable[PathType]] = None,
        notifier: Notifier = DEFAULT_NOTIFIER,
        indexer: AbstractVideoIndexer = None,
    ):
        super().__init__(db_folder, notifier=notifier)
        # Database content
        self._version = 2
        self.settings = DbSettings()
        self._date = Date.now()
        self._folders: Set[AbsolutePath] = set()
        self._videos: Dict[AbsolutePath, Video] = {}
        self._prop_types: Dict[str, PropType] = {}
        self._predictors: Dict[str, List[float]] = {}
        # Runtime
        self._id_to_video: Dict[int, Video] = {}
        self.moves_attribute = PotentialMoveAttribute(self)
        self._indexer = indexer or VideoIndexer(
            self.notifier, self.ways.db_index_pkl_path
        )
        self.in_save_context = False
        self._removed: Set[Video] = set()
        self._modified: Set[Video] = set()
        # Initialize
        self.__load(folders)
        # Initialize thumbnail manager.
        thumb_sql_path: AbsolutePath = self.ways.db_thumb_sql_path
        to_build = not thumb_sql_path.exists()
        self._thumb_mgr = ThumbnailManager(thumb_sql_path)
        if to_build:
            with Profiler("Build thumbnail SQL database", self.notifier):
                self._thumb_mgr.build(
                    self.select_videos_fields(
                        ["filename", "thumbnail_path"], "readable"
                    )
                )

    @Profiler.profile_method()
    def __load(self, folders: Optional[Iterable[PathType]] = None):
        to_save = False

        with Profiler("loading JSON file", self.notifier):
            # Loading JSON file
            backup = JsonBackup(self.ways.db_json_path, self.notifier)
            json_dict = backup.load()
            if not isinstance(json_dict, dict):
                raise exceptions.InvalidDatabaseJSON(backup.path)

        # Parsing version.
        version = json_dict.get("version", -1)
        assert version <= self._version
        if version < self._version:
            with Profiler("patch", self.notifier):
                patch_database_json(json_dict, version)
            to_save = True

        # Parsing settings.
        self.settings = DbSettings(json_dict.get("settings", {}))

        # Parsing date.
        if "date" in json_dict:
            self._date = Date(json_dict["date"])

        # Parsing folders.
        self._folders.update(
            AbsolutePath(path) for path in json_dict.get("folders", ())
        )
        if folders:
            lb = len(self._folders)
            self._folders.update(AbsolutePath.ensure(path) for path in folders)
            to_save = to_save or lb != len(self._folders)

        # Parsing video property types.
        for prop_dict in json_dict.get("prop_types", ()):
            prop_type = PropType.from_dict(prop_dict)
            assert prop_type.name not in self._prop_types
            self._prop_types[prop_type.name] = prop_type

        # Parsing predictors
        self._predictors = {
            name: predictor
            for name, predictor in json_dict.get("predictors", {}).items()
            if name in self._prop_types
        }

        # Parsing videos.
        with Profiler("parsing videos", self.notifier):
            folders_tree = PathTree(self._folders)
            self._videos = {
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
        self._indexer.build(self._videos.values())

        # Finish loading
        self.jsondb_save(on_new_identifiers=not to_save)
        self.notifier.notify(DatabaseLoaded(self))

    @Profiler.profile_method()
    def _jsondb_ensure_identifiers(self):
        id_to_video = {}  # type: Dict[int, Video]
        without_identifiers = []
        for video_state in self._videos.values():
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
        self._id_to_video = id_to_video
        if without_identifiers:
            logger.debug(f"Generating {len(without_identifiers)} new video indices.")
        return len(without_identifiers)

    @Profiler.profile_method()
    def jsondb_save(self, on_new_identifiers=False):
        """Save database on disk.

        Parameters
        ----------
        on_new_identifiers:
            if True, save only if new video IDs were generated.
        """
        # Update identifiers anyway
        identifiers_updated = self._jsondb_ensure_identifiers()
        # Do not save if in save context
        if self.in_save_context:
            logger.info("Saving deactivated in context.")
            return
        # Do not save if we must save only on new identifiers.
        if not identifiers_updated and on_new_identifiers:
            return
        # We can save. Save database.
        backup = JsonBackup(self.ways.db_json_path, self.notifier)
        backup.save(
            {
                "version": self._version,
                "settings": self.settings.to_dict(),
                "date": self._date.time,
                "folders": [folder.path for folder in self._folders],
                "prop_types": [prop.to_dict() for prop in self._prop_types.values()],
                "predictors": self._predictors,
                "videos": [video.to_dict() for video in self._videos.values()],
            }
        )
        self.notifier.notify(DatabaseSaved(self))

    def __close__(self):
        """Close database."""
        self._indexer.close()

    def to_save(self, to_save=True):
        return DatabaseToSaveContext(self, to_save=to_save)

    def jsondb_register_modified(self, video: Video):
        if video in self._removed:
            self._removed.remove(video)
        self._modified.add(video)

    def _jsondb_register_removed(self, video: Video):
        if video in self._modified:
            self._modified.remove(video)
        self._removed.add(video)

    def _jsondb_register_replaced(self, new_video: Video, old_video: Video):
        self._jsondb_register_removed(old_video)
        self.jsondb_register_modified(new_video)

    def _jsondb_flush_changes(self):
        # Prepare updating moves_attribute if having removed or added videos.
        nb_added = len(self._modified) - len(
            self._indexer.indexed_videos(self._modified)
        )
        self.moves_attribute.force_update = bool(
            self.moves_attribute.force_update or self._removed or nb_added
        )

        if self._removed:
            logger.info(f"Flushed {len(self._removed)} removed")
            self._indexer.remove_videos(self._removed)
        if self._modified:
            logger.info(f"Flushed {len(self._modified)} modified")
            self._indexer.update_videos(self._modified)
        self._removed.clear()
        self._modified.clear()

    def _jsondb_get_cached_videos(self, *flags, **forced_flags) -> List[Video]:
        if flags or forced_flags:
            self._jsondb_flush_changes()
            return [
                self._videos[filename]
                for filename in self._indexer.query_flags(
                    self._videos, *flags, **forced_flags
                )
            ]
        else:
            return list(self._videos.values())

    def get_settings(self) -> DbSettings:
        return self.settings

    def set_date(self, date: Date):
        self._date = date

    def set_folders(self, folders) -> None:
        folders = sorted(AbsolutePath.ensure(folder) for folder in folders)
        if folders == sorted(self._folders):
            return
        folders_tree = PathTree(folders)
        for video in self._videos.values():
            video.discarded = not folders_tree.in_folders(video.filename)
        self._folders = set(folders)
        self.jsondb_save()

    def get_folders(self) -> Iterable[AbsolutePath]:
        return iter(self._folders)

    def set_predictor(self, prop_name: str, theta: List[float]):
        self._predictors[prop_name] = theta
        self.jsondb_save()

    def get_predictor(self, prop_name):
        return self._predictors.get(prop_name, None)

    def count_videos(self, *flags, **forced_flags) -> int:
        if not flags and not forced_flags:
            return len(self._videos)
        else:
            return len(self._jsondb_get_cached_videos(*flags, **forced_flags))

    def select_videos_fields(
        self, fields: Sequence[str], *flags, **forced_flags
    ) -> Iterable[Dict[str, Any]]:
        return (
            {field: getattr(video, field) for field in fields}
            for video in self._jsondb_get_cached_videos(*flags, **forced_flags)
        )

    def has_prop_type(
        self, name, *, with_type=None, multiple=None, with_enum=None, default=None
    ) -> bool:
        if name not in self._prop_types:
            return False
        pt = self._prop_types[name]
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
            (prop.describe() for prop in self._prop_types.values()),
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
        if prop.name in self._prop_types:
            raise exceptions.PropertyAlreadyExists(prop.name)
        self._prop_types[prop.name] = prop
        self.jsondb_save()

    def remove_prop_type(self, name) -> None:
        if name in self._prop_types:
            del self._prop_types[name]
            for video in self._videos.values():
                video.remove_property(name)
            self.jsondb_save()

    def rename_prop_type(self, old_name, new_name) -> None:
        if self.has_prop_type(old_name):
            if self.has_prop_type(new_name):
                raise exceptions.PropertyAlreadyExists(new_name)
            prop_type = self._prop_types.pop(old_name)
            prop_type.name = new_name
            self._prop_types[new_name] = prop_type
            for video in self._videos.values():
                if video.has_property(old_name):
                    video.set_property(new_name, video.remove_property(old_name))
            self.jsondb_save()

    def convert_prop_to_unique(self, name) -> None:
        if self.has_prop_type(name):
            prop_type = self._prop_types[name]
            if not prop_type.multiple:
                raise exceptions.PropertyAlreadyUnique(name)
            for video in self._videos.values():
                if video.has_property(name) and len(video.get_property(name)) != 1:
                    raise exceptions.PropertyToUniqueError(
                        str(video.filename), name, video.get_property(name)
                    )
            prop_type.multiple = False
            # There should be nothing more to do.
            # For each video having this property,
            # there should already be a list with exactly 1 value.
            self.jsondb_save()

    def convert_prop_to_multiple(self, name) -> None:
        if self.has_prop_type(name):
            prop_type = self._prop_types[name]
            if prop_type.multiple:
                raise exceptions.PropertyAlreadyMultiple(name)
            prop_type.multiple = True
            # There should be nothing more to do.
            # Property value should already be a list
            # for videos having this property.
            self.jsondb_save()

    def get_prop_values(self, video_id: int, name: str) -> List[PropValueType]:
        return self._id_to_video[video_id].get_property(name)

    def set_prop_values(
        self, video_id: int, name: str, values: Union[Sequence, Set]
    ) -> None:
        video = self._id_to_video[video_id]
        if not values:
            video.remove_property(name)
        elif self._prop_types[name].multiple:
            video.set_property(name, self._prop_types[name].validate(values))
        else:
            (value,) = values
            video.set_property(name, self._prop_types[name].validate(value))

    def merge_prop_values(
        self, video_id: int, name: str, values: Union[Sequence, Set]
    ) -> None:
        pt = self._prop_types[name]
        if pt.multiple:
            values = pt.validate(
                self._id_to_video[video_id].get_property(name) + list(values)
            )
        self.set_prop_values(video_id, name, values)

    def validate_prop_values(self, name, values: list) -> List[PropValueType]:
        prop_type = self._prop_types[name]
        if prop_type.multiple:
            values = prop_type.validate(values)
        else:
            values = [prop_type.validate(value) for value in values]
        return values

    def set_video_properties(self, video_id: int, properties: dict) -> List[str]:
        modified = self._id_to_video[video_id].set_properties(
            {
                name: self._prop_types[name].validate(value)
                for name, value in properties.items()
            }
        )
        self._notify_properties_modified(modified)
        return modified

    def value_is_default(self, name: str, value: list) -> bool:
        pt = self._prop_types[name]
        return (not value) if pt.multiple else (value == [pt.default])

    def _update_videos_not_found(self, existing_paths: Container[AbsolutePath]):
        """Use given container of existing paths to mark not found videos."""
        for video_state in self._videos.values():
            video_state.found = video_state.filename in existing_paths

    def _notify_properties_modified(self, properties):
        self.jsondb_save()
        super()._notify_properties_modified(properties)

    def _notify_fields_modified(self, fields: Sequence[str]):
        self.jsondb_save()
        super()._notify_fields_modified(fields)

    def _jsondb_notify_filename_modified(self, new_video: Video, old_video: Video):
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
        self._jsondb_register_replaced(new_video, old_video)

    def _get_collectable_missing_thumbnails(self) -> Dict[str, int]:
        return {
            video["filename"].path: video["video_id"]
            for video in self.select_videos_fields(
                ["filename", "video_id"], "readable", "found"
            )
            if not self.jsondb_has_thumbnail(video["filename"])
        }

    def _notify_missing_thumbnails(self) -> None:
        super()._notify_missing_thumbnails()
        self.jsondb_save()

    def _find_video_paths_for_update(
        self, file_paths: Dict[AbsolutePath, VideoRuntimeInfo]
    ) -> List[str]:
        all_file_names = []
        for file_name, file_info in file_paths.items():
            video: Video = self._videos.get(file_name, None)
            if (
                video is None
                or file_info.mtime != video.runtime.mtime
                or file_info.size != video.file_size
                or file_info.driver_id != video.runtime.driver_id
                or (video.readable and not SpecialProperties.all_in(video))
                or self._video_must_be_updated(video)
            ):
                all_file_names.append(file_name.standard_path)
        all_file_names.sort()
        return all_file_names

    @classmethod
    def _video_must_be_updated(cls, video: Video):
        # A video readable with existing audio stream must have valid audio bits
        return video.readable and video.audio_codec and not video.audio_bits

    def get_all_video_indices(self) -> Iterable[int]:
        return self._id_to_video.keys()

    def has_video(self, **fields) -> bool:
        video = None
        if "filename" in fields:
            video = self._videos.get(fields.pop("filename"))
        elif "video_id" in fields:
            video = self._id_to_video.get(fields.pop("video_id"))
        return video and (
            not fields
            or all(getattr(video, field) == value for field, value in fields.items())
        )

    def get_video_terms(self, video_id: int) -> List[str]:
        return self._id_to_video[video_id].terms()

    def get_video_id(self, filename) -> int:
        return self._videos[AbsolutePath.ensure(filename)].video_id

    def read_video_field(self, video_id: int, field: str) -> Any:
        return getattr(self._id_to_video[video_id], field)

    def write_videos_field(self, indices: Iterable[int], field: str, values: Iterable):
        for video_id, value in zip(indices, values):
            setattr(self._id_to_video[video_id], field, value)

    def add_video_errors(self, video_id: int, *errors: Iterable[str]) -> None:
        self._id_to_video[video_id].add_errors(errors)

    def write_new_videos(
        self,
        video_entries: List[VideoEntry],
        runtime_info: Dict[AbsolutePath, VideoRuntimeInfo],
    ) -> None:
        videos: List[Video] = []
        unreadable: List[Video] = []
        for entry in video_entries:
            file_path = AbsolutePath.ensure(entry.filename)
            if entry.unreadable:
                video_state = Video.from_keys(
                    filename=file_path.path,
                    file_size=file_path.get_size(),
                    errors=sorted(entry.errors),
                    unreadable=True,
                    database=self,
                )
                unreadable.append(video_state)
            else:
                video_state = Video.from_keys(
                    **entry.to_formatted_dict(), database=self
                )
                # Get previous properties, if available
                if self.has_video(filename=file_path, readable=True):
                    old_video = self._videos[file_path]
                    video_state.properties = old_video.properties
                    video_state.similarity_id = old_video.similarity_id
                    video_state.video_id = old_video.video_id
                    video_state.thumb_name = old_video.thumb_name
                    video_state.date_entry_opened = old_video.date_entry_opened.time
                # Set special properties
                SpecialProperties.set(video_state)
            # Video modified, so automatically added to __modified.
            video_state.runtime = runtime_info[file_path]
            videos.append(video_state)
        self._videos.update({video.filename: video for video in videos})
        self.jsondb_save()
        if unreadable:
            self.notifier.notify(
                notifications.VideoInfoErrors(
                    {
                        video_state.filename: video_state.errors
                        for video_state in unreadable
                    }
                )
            )

    def change_video_entry_filename(
        self, video_id: int, path: AbsolutePath
    ) -> AbsolutePath:
        """Map video to new path in database.

        Return the previous path related to video.
        """
        path = AbsolutePath.ensure(path)
        assert path.isfile()
        video = self._id_to_video[video_id]
        assert video.readable
        assert video.filename != path

        del self._videos[video.filename]
        new_video = video.with_new_filename(path)
        self._videos[new_video.filename] = new_video
        self._id_to_video[video_id] = new_video
        self._jsondb_notify_filename_modified(new_video, video)

        self._thumb_mgr.rename(video.filename, new_video.filename)

        return video.filename

    def delete_video_entry(self, video_id: int) -> None:
        video = self._id_to_video.pop(video_id)
        self._videos.pop(video.filename, None)
        if video.readable:
            self._jsondb_old_get_thumbnail_path(video).delete()
        self._jsondb_register_removed(video)
        self.notifier.notify(notifications.VideoDeleted(video))
        self._notify_fields_modified(["move_id", "quality"])
        self._thumb_mgr.delete(video.filename)

    def move_video_entry(self, from_id, to_id) -> None:
        from_video = self._id_to_video[from_id]
        to_video = self._id_to_video[to_id]
        assert not from_video.found
        assert to_video.found
        for prop_name in self._prop_types.keys():
            self.merge_prop_values(
                to_id, prop_name, self.get_prop_values(from_id, prop_name)
            )
        to_video.similarity_id = from_video.similarity_id
        to_video.date_entry_modified = from_video.date_entry_modified.time
        to_video.date_entry_opened = from_video.date_entry_opened.time
        self.delete_video_entry(from_id)

    def confirm_unique_moves(self) -> int:
        with self.to_save() as saver:
            unique_moves = list(self.moves_attribute.get_unique_moves())
            for video_id, moves in unique_moves:
                self.move_video_entry(video_id, moves[0]["video_id"])
            saver.to_save = len(unique_moves)
        return len(unique_moves)

    def open_video(self, video_id: int) -> None:
        self._id_to_video[video_id].open()
        self._notify_fields_modified(["date_entry_opened"])

    @Profiler.profile_method()
    def describe_videos(self, video_indices: Sequence[int], with_moves=False):
        return [
            VideoFeatures.json(self._id_to_video[video_id], with_moves)
            for video_id in video_indices
        ]

    @Profiler.profile_method()
    def get_common_fields(self, video_indices: Iterable[int]) -> dict:
        return VideoFeatures.get_common_fields(
            self._id_to_video[video_id] for video_id in video_indices
        )

    def get_thumbnail_blob(self, filename: AbsolutePath):
        return self._thumb_mgr.get_blob(filename)

    def save_existing_thumbnails(self, filename_to_thumb_name: Dict[str, str]) -> None:
        self._thumb_mgr.save_existing_thumbnails(filename_to_thumb_name)

    def _jsondb_old_get_thumbnail_path(self, video: Video):
        return AbsolutePath.file_path(
            self.ways.db_thumb_folder, video.thumb_name, JPEG_EXTENSION
        )

    def jsondb_get_thumbnail_base64(self, filename: AbsolutePath) -> str:
        data = self._thumb_mgr.get_base64(filename)
        return ("data:image/jpeg;base64," + data.decode()) if data else None

    def jsondb_has_thumbnail(self, filename: AbsolutePath) -> bool:
        return self._thumb_mgr.has(filename)


class JsonDatabase(_JsonDatabase):
    """With methods used in database provider."""

    def search(
        self, text: str, cond: str = "and", videos: Sequence[int] = None
    ) -> Iterable[int]:
        if text:
            self._jsondb_flush_changes()
            if videos is None:
                filenames: Dict[AbsolutePath, Video] = self._videos
            else:
                filenames: Dict[AbsolutePath, Video] = {
                    self._id_to_video[video_id].filename: self._id_to_video[video_id]
                    for video_id in videos
                }
            terms = functions.string_to_pieces(text)
            if cond == "exact":
                with Profiler(f"query exact: {text}", self.notifier):
                    selection = (
                        filename
                        for filename in self._indexer.query_and(filenames, terms)
                        if self._videos[filename].has_exact_text(text)
                    )
            elif cond == "and":
                selection = self._indexer.query_and(filenames, terms)
            elif cond == "or":
                selection = self._indexer.query_or(filenames, terms)
            else:
                assert cond == "id"
                (term,) = terms
                video_id = int(term)
                selection = (
                    [self._id_to_video[video_id].filename]
                    if video_id in self._id_to_video
                    else []
                )
            return (filenames[filename].video_id for filename in selection)
        return ()

    def sort_video_indices(self, indices: Iterable[int], sorting: VideoSorting):
        return sorted(
            indices,
            key=lambda video_id: self._id_to_video[video_id].to_comparable(sorting),
        )

    def default_prop_unit(self, name):
        pt = self._prop_types[name]
        return None if pt.multiple else pt.default

    def __unused_clean_thumbnails(self, paths: List[AbsolutePath]):
        self._thumb_mgr.clean_thumbnails(paths)
