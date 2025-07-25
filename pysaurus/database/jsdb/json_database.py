import logging
from typing import Any, Collection, Iterable, Sequence

from pysaurus.application import exceptions
from pysaurus.core import functions, notifications
from pysaurus.core.components import AbsolutePath, Date, PathType
from pysaurus.core.functions import make_collection
from pysaurus.core.json_backup import JsonBackup
from pysaurus.core.notifying import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.db_utils import DatabaseLoaded
from pysaurus.database.jsdb.db_video_attribute import PotentialMoveAttribute
from pysaurus.database.jsdb.jsdb_prop_type import PropType
from pysaurus.database.jsdb.jsdb_video_provider import JsonDatabaseVideoProvider
from pysaurus.database.jsdb.jsdbvideo.abstract_video_indexer import AbstractVideoIndexer
from pysaurus.database.jsdb.jsdbvideo.lazy_video import LazyVideo as Video
from pysaurus.database.jsdb.jsdbvideo.video_indexer import VideoIndexer
from pysaurus.database.jsdb.json_database_utils import patch_database_json
from pysaurus.database.jsdb.thubmnail_database.thumbnail_manager import ThumbnailManager
from pysaurus.properties.properties import PropRawType, PropTypeValidator, PropUnitType
from pysaurus.video import VideoRuntimeInfo
from pysaurus.video.video_constants import VIDEO_FLAGS
from pysaurus.video.video_entry import VideoEntry
from pysaurus.video.video_pattern import VideoPattern
from pysaurus.video.video_sorting import VideoSorting

logger = logging.getLogger(__name__)


class JsonDatabase(AbstractDatabase):
    __slots__ = (
        "_version",
        "_date",
        "_folders",
        "_videos",
        "_prop_types",
        "_id_to_video",
        "moves_attribute",
        "_indexer",
        "_removed",
        "_modified",
        "_thumb_mgr",
    )

    def __init__(
        self,
        db_folder: PathType,
        folders: Iterable[PathType] | None = None,
        notifier: Notifier = DEFAULT_NOTIFIER,
        indexer: AbstractVideoIndexer = None,
    ):
        super().__init__(
            db_folder, notifier=notifier, provider=JsonDatabaseVideoProvider(self)
        )
        # Database content
        self._version = 2
        self._date = Date.now()
        self._folders: set[AbsolutePath] = set()
        self._videos: dict[AbsolutePath, Video] = {}
        self._prop_types: dict[str, PropType] = {}
        # Runtime
        self._id_to_video: dict[int, Video] = {}
        self.moves_attribute = PotentialMoveAttribute(self)
        self._indexer = indexer or VideoIndexer(
            self.notifier, self.ways.db_index_pkl_path
        )
        self._removed: set[Video] = set()
        self._modified: set[Video] = set()
        # Initialize thumbnail manager.
        thumb_sql_path: AbsolutePath = self.ways.db_thumb_sql_path
        to_build = not thumb_sql_path.exists()
        self._thumb_mgr = ThumbnailManager(thumb_sql_path)
        if to_build:
            with Profiler("Build thumbnail SQL database", self.notifier):
                self._thumb_mgr.build(
                    self.get_videos(
                        include=["filename", "thumbnail_path"], where={"readable": True}
                    )
                )
        # Initialize
        self.__jsondb_load(folders)

    @Profiler.profile_method()
    def __jsondb_load(self, folders: Iterable[PathType] | None = None):
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
        if to_save or self._jsondb_ensure_identifiers():
            self.save()
        self.notifier.notify(DatabaseLoaded(self))

    @Profiler.profile_method()
    def _jsondb_ensure_identifiers(self):
        id_to_video: dict[int, Video] = {}
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

    def jsondb_register_modified(self, video: Video):
        if video in self._removed:
            self._removed.remove(video)
        self._modified.add(video)

    def _jsondb_register_removed(self, video: Video):
        if video in self._modified:
            self._modified.remove(video)
        self._removed.add(video)

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
        if self._removed or self._modified:
            self._indexer.save()
        self._removed.clear()
        self._modified.clear()

    def jsondb_get_thumbnail_base64(self, filename: AbsolutePath) -> str:
        data = self._thumb_mgr.get_base64(filename)
        # return ("data:image/jpeg;base64," + data.decode()) if data else None
        return data.decode() if data else None

    def jsondb_has_thumbnail(self, filename: AbsolutePath) -> bool:
        return self._thumb_mgr.has(filename)

    def _jsondb_get_cached_videos(self, *flags, **forced_flags) -> list[Video]:
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

    def jsondb_prop_val_is_default(self, name: str, value: list) -> bool:
        pt = self._prop_types[name]
        return (not value) if pt.multiple else (value == [pt.default])

    def jsondb_get_thumbnail_blob(self, filename: AbsolutePath):
        return self._thumb_mgr.get_blob(filename)

    def jsondb_provider_search(
        self, text: str, cond: str = "and", videos: Sequence[int] = None
    ) -> Iterable[int]:
        if text:
            self._jsondb_flush_changes()
            if videos is None:
                filenames: dict[AbsolutePath, Video] = self._videos
            else:
                filenames: dict[AbsolutePath, Video] = {
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

    def jsondb_provider_sort_video_indices(
        self, indices: Iterable[int], sorting: VideoSorting
    ):
        return sorted(
            indices,
            key=lambda video_id: self._id_to_video[video_id].to_comparable(sorting),
        )

    def _jsondb_get_videos_from_identifiers(self, where: dict):
        q_video_id = where.pop("video_id", [])
        q_filename = where.pop("filename", [])

        if isinstance(q_video_id, int):
            q_video_id = [q_video_id]
        if isinstance(q_filename, AbsolutePath):
            q_filename = [q_filename]

        nb_expected = len(q_video_id) + len(q_filename)
        found = [
            self._id_to_video[video_id]
            for video_id in q_video_id
            if video_id in self._id_to_video
        ] + [
            self._videos[filename]
            for filename in q_filename
            if filename in self._videos
        ]
        return found, nb_expected

    @Profiler.profile_method()
    def _save(self):
        """Save database on disk."""
        JsonBackup(self.ways.db_json_path, self.notifier).save(
            {
                "version": self._version,
                "date": self._date.time,
                "folders": [folder.path for folder in self._folders],
                "prop_types": [prop.to_dict() for prop in self._prop_types.values()],
                "videos": [video.to_dict() for video in self._videos.values()],
            }
        )

    def _set_date(self, date: Date):
        self._date = date

    def _set_folders(self, folders: list[AbsolutePath]) -> None:
        folders_tree = PathTree(folders)
        for video in self._videos.values():
            video.discarded = not folders_tree.in_folders(video.filename)
        self._folders = set(folders)

    def get_folders(self) -> Iterable[AbsolutePath]:
        return iter(self._folders)

    def get_prop_types(
        self, *, name=None, with_type=None, multiple=None, with_enum=None, default=None
    ) -> list[dict]:
        if name is with_type is multiple is with_enum is default is None:
            prop_types = self._prop_types.values()
        else:
            prop_types = (
                pt
                for pt in self._prop_types.values()
                if (
                    (name is None or pt.name == name)
                    and (with_type is None or pt.type is with_type)
                    and (multiple is None or pt.multiple is multiple)
                    and (with_enum is None or pt.enumeration == sorted(set(with_enum)))
                    and (default is None or pt.default == default)
                )
            )
        return sorted((prop.describe() for prop in prop_types), key=lambda d: d["name"])

    def prop_type_add(
        self, name: str, prop_type: str | type, definition: PropRawType, multiple: bool
    ) -> None:
        prop = PropType.from_keys(
            **PropTypeValidator.define(name, prop_type, definition, multiple)
        )
        assert prop.type.__name__ == prop_type, (prop.type.__name__, prop_type)
        if prop.name in self._prop_types:
            raise exceptions.PropertyAlreadyExists(prop.name)
        self._prop_types[prop.name] = prop
        self.save()

    def prop_type_del(self, name) -> None:
        if name in self._prop_types:
            del self._prop_types[name]
            for video in self._videos.values():
                video.remove_property(name)
            self.save()

    def prop_type_set_name(self, old_name, new_name) -> None:
        if self.get_prop_types(name=old_name):
            if self.get_prop_types(name=new_name):
                raise exceptions.PropertyAlreadyExists(new_name)
            prop_type = self._prop_types.pop(old_name)
            prop_type.name = new_name
            self._prop_types[new_name] = prop_type
            for video in self._videos.values():
                if video.has_property(old_name):
                    video.set_property(new_name, video.remove_property(old_name))
            self.save()

    def prop_type_set_multiple(self, name: str, multiple: bool) -> None:
        if self.get_prop_types(name=name):
            prop_type = self._prop_types[name]
            if prop_type.multiple is multiple:
                raise exceptions.PropertyAlreadyMultiple(name, multiple)
            if not multiple:
                # Convert from multiple to unique.
                # Make sure videos does have only 1 value for this property.
                for video in self._videos.values():
                    if video.has_property(name) and len(video.get_property(name)) != 1:
                        raise exceptions.PropertyToUniqueError(
                            str(video.filename), name, video.get_property(name)
                        )
                pass
            prop_type.multiple = multiple
            self.save()

    def update_prop_values(
        self, video_id: int, name: str, values: Collection, *, merge=False
    ) -> bool:
        pt = self._prop_types[name]
        video = self._id_to_video[video_id]
        modified = False
        if values:
            if pt.multiple:
                if not merge:  # replace
                    modified = video.set_property(name, pt.validate(values))
                else:  # merge
                    new_values = pt.validate(video.get_property(name) + list(values))
                    modified = video.set_property(name, new_values)
            else:  # merge == replace
                (value,) = values
                modified = video.set_property(name, pt.validate(value))
        elif not merge:  # replace with empty -> remove
            modified = video.remove_property(name)
        return modified

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
        # JSON database: register replaced
        self._jsondb_register_removed(old_video)
        self.jsondb_register_modified(new_video)

    def get_videos(
        self,
        *,
        include: Sequence[str] = None,
        with_moves: bool = False,
        where: dict = None,
    ) -> list[VideoPattern]:
        where = where or {}
        # where["discarded"] = where.get("discarded", False)
        q_flags = {key: value for key, value in where.items() if key in VIDEO_FLAGS}
        q_other = {key: value for key, value in where.items() if key not in VIDEO_FLAGS}

        i_videos, nb_expected = self._jsondb_get_videos_from_identifiers(q_other)
        if not nb_expected:
            base_videos = self._videos.values()
            if q_flags:
                base_videos = self._jsondb_get_cached_videos(**q_flags)
        else:
            base_videos = i_videos
            if q_flags:
                base_videos = (
                    video
                    for video in i_videos
                    if all(
                        getattr(video, flag) is value for flag, value in q_flags.items()
                    )
                )

        videos = base_videos
        if q_other:
            videos = (
                video
                for video in base_videos
                if all(getattr(video, key) == value for key, value in q_other.items())
            )

        return list(videos)

    def videos_get_terms(self) -> dict[int, list[str]]:
        return {
            video_id: self._id_to_video[video_id].terms()
            for video_id in self._get_all_video_indices()
        }

    def videos_set_field(self, field: str, changes: dict[int, Any]):
        for video_id, value in changes.items():
            setattr(self._id_to_video[video_id], field, value)

    def videos_add(
        self,
        video_entries: list[VideoEntry],
        runtime_info: dict[AbsolutePath, VideoRuntimeInfo],
    ) -> None:
        videos: list[Video] = []
        unreadable: list[Video] = []
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
                    video_state.date_entry_opened = old_video.date_entry_opened.time
            video_state.runtime = runtime_info[file_path]
            videos.append(video_state)
        self._videos.update({video.filename: video for video in videos})
        self._jsondb_ensure_identifiers()
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

    def video_entry_set_filename(
        self, video_id: int, path: AbsolutePath
    ) -> AbsolutePath:
        path = AbsolutePath.ensure(path)
        assert path.isfile()
        video = self._id_to_video[video_id]
        assert video.readable
        assert video.filename != path

        del self._videos[video.filename]
        new_video = video.with_new_filename(path)
        self._videos[new_video.filename] = new_video
        self._id_to_video[video_id] = new_video
        self._thumb_mgr.rename(video.filename, new_video.filename)

        self._notify_filename_modified(new_video, video)

        return video.filename

    def video_entry_del(self, video_id: int) -> None:
        video = self._id_to_video.pop(video_id)
        self._videos.pop(video.filename, None)
        self._jsondb_register_removed(video)
        self._thumb_mgr.delete(video.filename)
        self.provider.delete(video_id)
        self._notify_fields_modified(["move_id"])

    def videos_get_moves(self) -> Iterable[tuple[int, list[dict]]]:
        return self.moves_attribute.get_moves()

    def _thumbnails_add(self, filename_to_thumb_name: dict[str, str]) -> None:
        self._thumb_mgr.save_existing_thumbnails(filename_to_thumb_name)
        for filename in filename_to_thumb_name:
            self.jsondb_register_modified(self._videos[AbsolutePath.ensure(filename)])

    def videos_tag_get(
        self, name: str, indices: list[int] = ()
    ) -> dict[int, list[PropUnitType]]:
        return {
            video_id: self._id_to_video[video_id].get_property(name)
            for video_id in (indices or self._get_all_video_indices())
        }

    def _get_all_video_indices(self) -> Iterable[int]:
        return (item.video_id for item in self.get_videos(include=["video_id"]))

    def videos_tag_set(
        self, name: str, updates: dict[int, Collection[PropUnitType]], merge=False
    ):
        for video_id, prop_values in updates.items():
            self.update_prop_values(video_id, name, prop_values, merge=merge)

    def video_entry_set_tags(
        self, video_id: int, properties: dict, merge=False
    ) -> None:
        modified = [
            name
            for name, values in properties.items()
            if self.update_prop_values(
                video_id, name, make_collection(values), merge=merge
            )
        ]
        self._notify_fields_modified(modified, is_property=True)

    def default_prop_unit(self, name):
        (pt,) = self.get_prop_types(name=name)
        return None if pt["multiple"] else pt["defaultValues"][0]
