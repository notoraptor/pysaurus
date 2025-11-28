"""
NewSqlDatabase - High-level SQL database implementation.

This class inherits from AbstractDatabase and uses SqlDatabase internally
for all storage operations.
"""

import logging
from typing import Any, Collection, Iterable, Sequence

from pysaurus.core.absolute_path import AbsolutePath, PathType
from pysaurus.core.classes import Text
from pysaurus.core.datestring import Date
from pysaurus.core.functions import string_to_pieces
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.db_utils import DatabaseLoaded
from pysaurus.database.newsql.sql_database import SqlDatabase
from pysaurus.properties.properties import PropRawType, PropUnitType
from pysaurus.video import VideoRuntimeInfo
from pysaurus.video.video_entry import VideoEntry
from pysaurus.video.video_pattern import VideoPattern
from pysaurus.video.video_sorting import VideoSorting

logger = logging.getLogger(__name__)


class SqlVideo(VideoPattern):
    """
    Video wrapper that provides VideoPattern interface over SQL data.

    This class wraps the raw dict data from SQL and provides attribute
    access compatible with the rest of the codebase.
    """

    __slots__ = ("_data", "_video_id", "_filename", "_database")

    def __init__(
        self, video_id: int, filename: str, data: dict, database: "NewSqlDatabase"
    ):
        self._video_id = video_id
        self._filename = AbsolutePath.ensure(filename)
        self._data = data
        self._database = database

    @property
    def video_id(self) -> int:
        return self._video_id

    @property
    def filename(self) -> AbsolutePath:
        return self._filename

    @property
    def file_size(self) -> int:
        return self._data.get("s") or self._data.get("file_size", 0)

    @property
    def errors(self) -> list:
        return self._data.get("e") or self._data.get("errors", [])

    @property
    def unreadable(self) -> bool:
        return self._data.get("U", self._data.get("unreadable", False))

    @property
    def readable(self) -> bool:
        return not self.unreadable

    @property
    def meta_title(self) -> Text:
        return Text(self._data.get("n") or self._data.get("meta_title", ""))

    @property
    def properties(self) -> dict:
        return self._data.get("p") or self._data.get("properties", {})

    @property
    def similarity_id(self) -> int | None:
        # Use explicit None check because 0 is a valid value
        val = self._data.get("S")
        if val is not None:
            return val
        return self._data.get("similarity_id")

    @property
    def watched(self) -> bool:
        return self._data.get("O", self._data.get("watched", False))

    @property
    def date_entry_modified(self) -> Date:
        val = self._data.get("m") or self._data.get("date_entry_modified", 0)
        return Date(val)

    @property
    def date_entry_opened(self) -> Date:
        val = self._data.get("o") or self._data.get("date_entry_opened", 0)
        return Date(val)

    @property
    def already_opened(self) -> bool:
        return self.date_entry_opened.time > 0

    # Runtime info properties
    @property
    def _runtime(self) -> dict:
        return self._data.get("R") or self._data.get("runtime", {})

    @property
    def found(self) -> bool:
        r = self._runtime
        if isinstance(r, dict):
            return r.get("f", r.get("is_file", True))
        return False

    @property
    def not_found(self) -> bool:
        return not self.found

    @property
    def mtime(self) -> float:
        r = self._runtime
        if isinstance(r, dict):
            return r.get("m", r.get("mtime", 0))
        return 0

    @property
    def driver_id(self) -> int:
        r = self._runtime
        if isinstance(r, dict):
            return r.get("d", r.get("driver_id", 0))
        return 0

    # Video technical properties
    @property
    def duration(self) -> int:
        return self._data.get("d") or self._data.get("duration", 0)

    @property
    def duration_time_base(self) -> int:
        return self._data.get("t") or self._data.get("duration_time_base", 1000000)

    @property
    def raw_microseconds(self) -> int:
        return (
            int(self.duration * 1000000 / self.duration_time_base)
            if self.duration_time_base
            else 0
        )

    @property
    def width(self) -> int:
        return self._data.get("w") or self._data.get("width", 0)

    @property
    def height(self) -> int:
        return self._data.get("h") or self._data.get("height", 0)

    @property
    def audio_codec(self) -> Text:
        # Short key: "a"
        return Text(self._data.get("a") or self._data.get("audio_codec", ""))

    @property
    def video_codec(self) -> Text:
        # Short key: "v"
        return Text(self._data.get("v") or self._data.get("video_codec", ""))

    @property
    def container_format(self) -> Text:
        # Short key: "c"
        return Text(self._data.get("c") or self._data.get("container_format", ""))

    @property
    def frame_rate_num(self) -> int:
        # Short key: "x"
        return self._data.get("x") or self._data.get("frame_rate_num", 0)

    @property
    def frame_rate_den(self) -> int:
        # Short key: "y"
        return self._data.get("y") or self._data.get("frame_rate_den", 1)

    @property
    def audio_bit_rate(self) -> int:
        # Short key: "r"
        return self._data.get("r") or self._data.get("audio_bit_rate", 0)

    @property
    def sample_rate(self) -> int:
        # Short key: "u"
        return self._data.get("u") or self._data.get("sample_rate", 0)

    @property
    def channels(self) -> int:
        # Short key: "C"
        return self._data.get("C") or self._data.get("channels", 0)

    @property
    def audio_bits(self) -> int:
        # Short key: "B"
        return self._data.get("B") or self._data.get("audio_bits", 0)

    @property
    def audio_codec_description(self) -> Text:
        # Short key: "A"
        return Text(
            self._data.get("A") or self._data.get("audio_codec_description", "")
        )

    @property
    def video_codec_description(self) -> Text:
        # Short key: "V"
        return Text(
            self._data.get("V") or self._data.get("video_codec_description", "")
        )

    @property
    def bit_depth(self) -> int:
        # Short key: "D"
        return self._data.get("D") or self._data.get("bit_depth", 0)

    @property
    def device_name(self) -> Text:
        # Short key: "b"
        return Text(self._data.get("b") or self._data.get("device_name", ""))

    @property
    def audio_languages(self) -> list[str]:
        # Short key: "l"
        return self._data.get("l") or self._data.get("audio_languages", [])

    @property
    def subtitle_languages(self) -> list[str]:
        # Short key: "L"
        return self._data.get("L") or self._data.get("subtitle_languages", [])

    @property
    def moves(self) -> list:
        # Moves are computed dynamically via database.moves_attribute
        return self._database.moves_attribute(self._video_id)[1]

    @property
    def move_id(self):
        # Move ID is computed dynamically via database.moves_attribute
        return self._database.moves_attribute(self._video_id)[0]

    # Derived properties
    @property
    def title(self) -> Text:
        return self.meta_title if self.meta_title else Text(self._filename.file_title)

    @property
    def file_title(self) -> Text:
        return Text(self._filename.file_title)

    @property
    def extension(self) -> str:
        return self._filename.extension

    @property
    def disk(self):
        # Match LazyVideo: get_drive_name() or driver_id
        return self._filename.get_drive_name() or self.driver_id

    @property
    def with_thumbnails(self) -> bool:
        return self._database.has_thumbnail(self._filename)

    @property
    def without_thumbnails(self) -> bool:
        return not self.with_thumbnails

    @property
    def thumbnail(self) -> bytes | None:
        return self._database.get_thumbnail_blob(self._filename)

    @property
    def thumbnail_base64(self) -> str:
        return self._database.get_thumbnail_base64(self._filename)

    @property
    def discarded(self) -> bool:
        # Computed based on whether filename is in monitored folders
        return self._database._is_discarded(self._filename)

    def has_exact_text(self, text: str) -> bool:
        """Check if video contains exact text (case-insensitive)."""
        text_lower = text.lower()
        if text_lower in self._filename.path.lower():
            return True
        if text_lower in self.meta_title.value.lower():
            return True
        for values in self.properties.values():
            for value in values:
                if isinstance(value, str) and text_lower in value.lower():
                    return True
        return False

    def to_comparable(self, sorting: VideoSorting) -> list:
        """Return a list for sorting comparison."""
        from pysaurus.core.compare import to_comparable

        return [
            to_comparable(getattr(self, field, None), reverse)
            for field, reverse in sorting
        ]


class NewSqlDatabase(AbstractDatabase):
    """
    SQL-based database implementation.

    Uses SqlDatabase internally for storage, provides AbstractDatabase interface.
    """

    __slots__ = ("_sql", "_folders", "_prop_types_cache", "_date", "moves_attribute")

    def __init__(self, db_folder: PathType, notifier=DEFAULT_NOTIFIER):
        # Import here to avoid circular imports
        from pysaurus.database.jsdb.db_video_attribute import PotentialMoveAttribute
        from pysaurus.database.jsdb.jsdb_video_provider import JsonDatabaseVideoProvider

        # Initialize SqlDatabase
        db_folder = AbsolutePath.ensure(db_folder).assert_dir()
        sql_path = db_folder / "newsql.db"

        if not sql_path.exists():
            raise FileNotFoundError(
                f"SQL database not found: {sql_path}. "
                f"Run migration first with: migrate_database_folder('{db_folder}')"
            )

        self._sql = SqlDatabase(sql_path.path)

        # Load folders
        self._folders = set(AbsolutePath.ensure(f) for f in self._sql.get_folders())

        # Cache prop_types
        self._prop_types_cache: dict[str, dict] | None = None

        # Load date
        self._date = Date(self._sql.get_config("date") or 0)

        # Initialize moves_attribute (like JsonDatabase)
        self.moves_attribute = PotentialMoveAttribute(self)

        # Initialize parent with provider
        # Note: provider expects a database, we pass self
        provider = JsonDatabaseVideoProvider(self)
        super().__init__(db_folder, provider, notifier)

        # Notify loaded
        self.notifier.notify(DatabaseLoaded(self))

    @classmethod
    def from_memory_copy(
        cls, db_folder: PathType, notifier=DEFAULT_NOTIFIER
    ) -> "NewSqlDatabase":
        """
        Create an in-memory copy of an existing NewSqlDatabase.

        The SQLite database is loaded entirely into memory using sqlite3.backup().
        This is much faster for tests than copying files to a temp directory.
        All modifications are done in memory and don't affect the original file.
        """
        from pysaurus.database.jsdb.db_video_attribute import PotentialMoveAttribute
        from pysaurus.database.jsdb.jsdb_video_provider import JsonDatabaseVideoProvider

        db_folder = AbsolutePath.ensure(db_folder).assert_dir()
        sql_path = db_folder / "newsql.db"

        if not sql_path.exists():
            raise FileNotFoundError(f"SQL database not found: {sql_path}")

        # Create instance without calling __init__
        instance = object.__new__(cls)

        # Initialize SqlDatabase from memory copy
        instance._sql = SqlDatabase.from_memory_copy(sql_path.path)

        # Load folders
        instance._folders = set(
            AbsolutePath.ensure(f) for f in instance._sql.get_folders()
        )

        # Cache prop_types
        instance._prop_types_cache = None

        # Load date
        instance._date = Date(instance._sql.get_config("date") or 0)

        # Initialize moves_attribute
        instance.moves_attribute = PotentialMoveAttribute(instance)

        # Initialize parent with provider
        provider = JsonDatabaseVideoProvider(instance)
        AbstractDatabase.__init__(instance, db_folder, provider, notifier)

        # Notify loaded
        instance.notifier.notify(DatabaseLoaded(instance))

        return instance

    def __close__(self):
        super().__close__()
        self._sql.close()

    # =========================================================================
    # Abstract methods implementation
    # =========================================================================

    def _set_date(self, date: Date):
        self._date = date
        self._sql.set_config("date", date.time)

    def get_folders(self) -> Iterable[AbsolutePath]:
        return self._folders

    def _set_folders(self, folders: list[AbsolutePath]) -> None:
        self._folders = set(folders)
        self._sql.set_folders([f.path for f in folders])

    def get_prop_types(
        self, *, name=None, with_type=None, multiple=None, with_enum=None, default=None
    ) -> list[dict]:
        # Refresh cache if needed
        if self._prop_types_cache is None:
            self._prop_types_cache = {
                pt["name"]: pt for pt in self._sql.get_prop_types()
            }

        results = []
        for pt in self._prop_types_cache.values():
            # Filter by name
            if name is not None and pt["name"] != name:
                continue

            # Determine type from definition
            definition = pt["definition"]
            if definition is None:
                pt_type = str
            elif isinstance(definition, bool):
                pt_type = bool
            elif isinstance(definition, int):
                pt_type = int
            elif isinstance(definition, float):
                pt_type = float
            elif isinstance(definition, str):
                pt_type = str
            elif isinstance(definition, list):
                if definition:
                    pt_type = type(definition[0])
                else:
                    pt_type = str
            else:
                pt_type = str

            # Filter by type
            if with_type is not None and pt_type != with_type:
                continue

            # Filter by multiple
            if multiple is not None and pt["multiple"] != multiple:
                continue

            # Filter by enum (has list definition)
            if with_enum is not None:
                has_enum = isinstance(definition, list) and len(definition) > 0
                if has_enum != with_enum:
                    continue

            # Filter by default
            if default is not None:
                pt_default = (
                    definition
                    if not isinstance(definition, list)
                    else (definition[0] if definition else None)
                )
                if pt_default != default:
                    continue

            # Build result dict matching expected format
            results.append(
                {
                    "name": pt["name"],
                    "type": pt_type.__name__,
                    "definition": definition,
                    "multiple": pt["multiple"],
                    "defaultValue": definition
                    if not isinstance(definition, list)
                    else (definition[0] if definition else None),
                    "enumeration": definition if isinstance(definition, list) else None,
                }
            )

        return results

    def prop_type_add(
        self, name: str, prop_type: str | type, definition: PropRawType, multiple: bool
    ) -> None:
        self._sql.set_prop_type(name, definition, multiple)
        self._prop_types_cache = None  # Invalidate cache
        self.save()

    def prop_type_del(self, name):
        self._sql.delete_prop_type(name)
        self._prop_types_cache = None
        # Remove property from all videos
        for video in self._sql.get_all_videos():
            data = video["data"]
            props = data.get("p") or data.get("properties", {})
            if name in props:
                del props[name]
                self._sql.update_video(video["video_id"], data)
        self.save()

    def prop_type_set_name(self, old_name, new_name):
        self._sql.rename_prop_type(old_name, new_name)
        self._prop_types_cache = None
        # Rename in all videos
        for video in self._sql.get_all_videos():
            data = video["data"]
            props = data.get("p") or data.get("properties", {})
            if old_name in props:
                props[new_name] = props.pop(old_name)
                self._sql.update_video(video["video_id"], data)
        self.save()

    def prop_type_set_multiple(self, name: str, multiple: bool) -> None:
        pt = self._sql.get_prop_type(name)
        if pt:
            self._sql.set_prop_type(name, pt["definition"], multiple)
            self._prop_types_cache = None
            self.save()

    @Profiler.profile_method()
    def get_videos(
        self,
        *,
        include: Sequence[str] = None,
        with_moves: bool = False,
        where: dict = None,
    ) -> list[VideoPattern]:
        where = dict(where) if where else {}

        # Handle video_id filter
        video_ids = where.pop("video_id", None)
        if video_ids is not None:
            if isinstance(video_ids, int):
                video_ids = [video_ids]
            elif isinstance(video_ids, (list, tuple)):
                video_ids = list(video_ids)

        # Handle filename filter
        filenames = where.pop("filename", None)
        if filenames is not None:
            if isinstance(filenames, AbsolutePath):
                filenames = [filenames.path]
            elif isinstance(filenames, (list, tuple)):
                filenames = [
                    f.path if isinstance(f, AbsolutePath) else f for f in filenames
                ]

        # Get videos from SQL
        if video_ids is not None:
            videos = [self._sql.get_video_by_id(vid) for vid in video_ids]
            videos = [v for v in videos if v is not None]
        elif filenames is not None:
            videos = [self._sql.get_video_by_filename(f) for f in filenames]
            videos = [v for v in videos if v is not None]
        else:
            videos = self._sql.get_all_videos()

        # Wrap as SqlVideo
        results = [
            SqlVideo(v["video_id"], v["filename"], v["data"], self) for v in videos
        ]

        # Apply remaining filters
        for key, value in where.items():
            results = [v for v in results if self._video_matches_filter(v, key, value)]

        return results

    def _video_matches_filter(self, video: SqlVideo, key: str, value: Any) -> bool:
        """Check if video matches a filter criterion."""
        video_value = getattr(video, key, None)
        if video_value is None:
            return value is None
        if isinstance(value, (list, tuple)):
            return video_value in value
        return video_value == value

    def _is_discarded(self, filename: AbsolutePath) -> bool:
        """Check if filename is outside monitored folders."""
        folders_tree = PathTree(self._folders)
        return not folders_tree.in_folders(filename)

    def videos_get_terms(self) -> dict[int, list[str]]:
        # Get string property type names for including property values in terms
        string_prop_names = {
            pt["name"] for pt in self.get_prop_types() if pt.get("type") == "str"
        }

        result = {}
        for video in self._sql.get_all_videos():
            video_id = video["video_id"]
            data = video["data"]
            filename = video["filename"]
            meta_title = data.get("n") or data.get("meta_title", "")

            # Start with filename and meta_title
            term_sources = [filename, meta_title]

            # Add string property values (same as lazy_video.terms())
            props = data.get("p") or data.get("properties", {})
            for prop_name in string_prop_names:
                if prop_name in props:
                    values = props[prop_name]
                    if isinstance(values, list):
                        term_sources.extend(str(v) for v in values)
                    else:
                        term_sources.append(str(values))

            all_str = " ".join(term_sources)
            t_all_str = string_to_pieces(all_str)
            t_all_str_low = string_to_pieces(all_str.lower())
            terms = (
                t_all_str if t_all_str == t_all_str_low else (t_all_str + t_all_str_low)
            )
            result[video_id] = terms
        return result

    def videos_get_moves(self) -> Iterable[tuple[int, list[dict]]]:
        # Delegate to moves_attribute (same as JsonDatabase)
        return self.moves_attribute.get_moves()

    def video_entry_del(self, video_id: int) -> None:
        video = self._sql.get_video_by_id(video_id)
        if video:
            filename = video["filename"]
            self._sql.delete_video(video_id)
            self._sql.delete_thumbnail(filename)
            self._sql.remove_search_terms(filename)
            self._sql.remove_video_flags(filename)
            self.save()

    def video_entry_set_filename(
        self, video_id: int, path: AbsolutePath
    ) -> AbsolutePath:
        video = self._sql.get_video_by_id(video_id)
        if not video:
            raise ValueError(f"Video not found: {video_id}")

        old_filename = video["filename"]
        new_filename = path.path

        # Update data
        data = video["data"]
        if "f" in data:
            data["f"] = new_filename
        else:
            data["filename"] = new_filename

        # Update in SQL
        self._sql.update_video_filename(video_id, new_filename, data)
        self._sql.rename_thumbnail(old_filename, new_filename)

        # Update search index
        self._sql.remove_search_terms(old_filename)
        self._sql.remove_video_flags(old_filename)
        self._update_video_index(video_id, new_filename, data)

        # Rename actual file
        old_path = AbsolutePath.ensure(old_filename)
        if old_path.exists():
            old_path.rename(path)

        self.save()
        return old_path

    def videos_set_field(self, field: str, changes: dict[int, Any]):
        if not changes:
            return

        # Map field names to short keys
        field_map = {
            "found": ("R", "f"),  # runtime.is_file
            "similarity_id": ("S", None),
            "date_entry_modified": ("m", None),
            "date_entry_opened": ("o", None),
            "watched": ("O", None),
        }

        for video_id, value in changes.items():
            video = self._sql.get_video_by_id(video_id)
            if not video:
                continue

            data = video["data"]
            filename = video["filename"]

            if field == "found":
                # Update runtime.is_file
                runtime = data.get("R") or data.get("runtime", {})
                if not isinstance(runtime, dict):
                    runtime = {}
                runtime["f"] = value
                data["R"] = runtime
            elif field in field_map:
                short_key = field_map[field][0]
                if short_key in data:
                    data[short_key] = value
                else:
                    data[field] = value
            else:
                data[field] = value

            self._sql.update_video(video_id, data)
            self._update_video_index(video_id, filename, data)

        self.save()

    def videos_add(
        self,
        video_entries: list[VideoEntry],
        runtime_info: dict[AbsolutePath, VideoRuntimeInfo],
    ) -> None:
        for entry in video_entries:
            filename = entry.filename
            info = runtime_info.get(filename)

            # Check if video exists
            existing = self._sql.get_video_by_filename(filename.path)
            if existing:
                video_id = existing["video_id"]
                data = existing["data"]
            else:
                video_id = self._sql.get_next_video_id()
                data = {}

            # Update data from entry
            data["f"] = filename.path
            data["s"] = entry.file_size
            data["e"] = entry.errors
            data["j"] = video_id
            data["U"] = entry.unreadable

            if not entry.unreadable:
                # Use correct short keys from VIDEO_SCHEMA
                data["d"] = entry.duration
                data["t"] = entry.duration_time_base
                data["w"] = entry.width
                data["h"] = entry.height
                data["a"] = entry.audio_codec  # "a" not "A"
                data["v"] = entry.video_codec  # "v" not "V"
                data["c"] = entry.container_format  # "c" not "C"
                data["x"] = entry.frame_rate_num  # "x" not "rn"
                data["y"] = entry.frame_rate_den  # "y" not "rd"
                data["r"] = entry.audio_bit_rate  # "r" not "ab"
                data["u"] = entry.sample_rate  # "u" not "sr"
                data["C"] = entry.channels  # "C" not "c"
                data["n"] = entry.meta_title

            # Add runtime info
            if info:
                data["R"] = {
                    "s": info.size,
                    "m": info.mtime,
                    "d": info.driver_id,
                    "f": info.is_file,
                }

            # Preserve properties if existing
            if "p" not in data and "properties" not in data:
                data["p"] = {}

            # Insert or update
            if existing:
                self._sql.update_video(video_id, data)
            else:
                self._sql.insert_video(video_id, filename.path, data)

            # Update index
            self._update_video_index(video_id, filename.path, data)

        self.save()

    def _thumbnails_add(self, filename_to_thumb_name: dict[str, str]) -> None:
        for filename, thumb_path in filename_to_thumb_name.items():
            with open(thumb_path, "rb") as f:
                blob = f.read()
            self._sql.set_thumbnail(filename, blob)
            # Update index flag
            self._sql.execute(
                "UPDATE video_flags SET value = 1 WHERE filename = ? AND flag = 'with_thumbnails'",
                (filename,),
            )
            self._sql.execute(
                "UPDATE video_flags SET value = 0 WHERE filename = ? AND flag = 'without_thumbnails'",
                (filename,),
            )

    def videos_tag_get(
        self, name: str, indices: list[int] = ()
    ) -> dict[int, list[PropUnitType]]:
        result = {}
        if indices:
            videos = [self._sql.get_video_by_id(vid) for vid in indices]
            videos = [v for v in videos if v is not None]
        else:
            videos = self._sql.get_all_videos()

        for video in videos:
            video_id = video["video_id"]
            data = video["data"]
            props = data.get("p") or data.get("properties", {})
            result[video_id] = list(props.get(name, []))

        return result

    def video_entry_set_tags(
        self, video_id: int, properties: dict, merge=False
    ) -> None:
        video = self._sql.get_video_by_id(video_id)
        if not video:
            return

        data = video["data"]
        props = data.get("p") or data.get("properties", {})

        for name, values in properties.items():
            if merge:
                existing = set(props.get(name, []))
                existing.update(values)
                props[name] = sorted(existing)
            else:
                props[name] = sorted(values)

        data["p"] = props
        self._sql.update_video(video_id, data)
        self._update_video_index(video_id, video["filename"], data)
        self.save()

    def videos_tag_set(
        self, name: str, updates: dict[int, Collection[PropUnitType]], merge=False
    ):
        if not updates:
            return

        # Batch fetch all videos at once
        all_videos = {v["video_id"]: v for v in self._sql.get_all_videos()}

        # Collect all updates
        batch_updates = []  # [(video_id, data, filename), ...]
        for video_id, values in updates.items():
            video = all_videos.get(video_id)
            if not video:
                continue

            data = video["data"]
            props = data.get("p") or data.get("properties", {})

            if merge:
                existing = set(props.get(name, []))
                existing.update(values)
                props[name] = sorted(existing)
            else:
                props[name] = sorted(values)

            data["p"] = props
            batch_updates.append((video_id, data, video["filename"]))

        # Batch update all videos
        self._sql.update_videos_batch(batch_updates)

        # Batch update indexes
        for video_id, data, filename in batch_updates:
            self._update_video_index(video_id, filename, data)

        self.save()

    # =========================================================================
    # Provider methods (called by JsonDatabaseVideoProvider)
    # =========================================================================

    def has_thumbnail(self, filename: AbsolutePath) -> bool:
        return self._sql.has_thumbnail(filename.path)

    def get_thumbnail_blob(self, filename: AbsolutePath) -> bytes | None:
        return self._sql.get_thumbnail(filename.path)

    def get_thumbnail_base64(self, filename: AbsolutePath) -> str:
        import base64

        blob = self._sql.get_thumbnail(filename.path)
        if blob:
            return base64.b64encode(blob).decode("ascii")
        return ""

    def default_prop_unit(self, name: str):
        """Return default value for a property."""
        pt = self._sql.get_prop_type(name)
        if pt:
            definition = pt["definition"]
            if isinstance(definition, list) and definition:
                return definition[0]
            return definition
        return None

    def jsondb_get_thumbnail_base64(self, filename: AbsolutePath) -> str:
        return self.get_thumbnail_base64(filename)

    def jsondb_has_thumbnail(self, filename: AbsolutePath) -> bool:
        return self.has_thumbnail(filename)

    def jsondb_prop_val_is_default(self, name: str, value: list) -> bool:
        pt_list = self.get_prop_types(name=name)
        if not pt_list:
            return True
        pt = pt_list[0]
        if pt["multiple"]:
            return not value
        return value == [pt["defaultValue"]]

    def jsondb_get_thumbnail_blob(self, filename: AbsolutePath):
        return self.get_thumbnail_blob(filename)

    def jsondb_provider_search(
        self, text: str, cond: str = "and", videos: Sequence[int] = None
    ) -> Iterable[int]:
        if not text:
            return ()

        terms = string_to_pieces(text)

        if cond == "id":
            # Search by video ID
            try:
                video_id = int(terms[0])
                if self._sql.get_video_by_id(video_id):
                    return [video_id]
            except (ValueError, IndexError):
                pass
            return ()

        # Get filenames from terms
        if cond == "and":
            filenames = self._sql.query_terms_and(terms)
        elif cond == "or":
            filenames = self._sql.query_terms_or(terms)
        elif cond == "exact":
            filenames = self._sql.query_terms_and(terms)
            # Filter for exact match
            filenames = {f for f in filenames if self._has_exact_text(f, text)}
        else:
            return ()

        # Filter by video_ids if provided
        if videos is not None:
            video_id_set = set(videos)
            result = []
            for filename in filenames:
                video = self._sql.get_video_by_filename(filename)
                if video and video["video_id"] in video_id_set:
                    result.append(video["video_id"])
            return result

        # Return all matching video IDs
        result = []
        for filename in filenames:
            video = self._sql.get_video_by_filename(filename)
            if video:
                result.append(video["video_id"])
        return result

    def _has_exact_text(self, filename: str, text: str) -> bool:
        """Check if video contains exact text."""
        video = self._sql.get_video_by_filename(filename)
        if not video:
            return False
        sv = SqlVideo(video["video_id"], filename, video["data"], self)
        return sv.has_exact_text(text)

    def jsondb_provider_sort_video_indices(
        self, indices: Iterable[int], sorting: VideoSorting
    ):
        videos = []
        for video_id in indices:
            video = self._sql.get_video_by_id(video_id)
            if video:
                sv = SqlVideo(video["video_id"], video["filename"], video["data"], self)
                videos.append((video_id, sv))

        videos.sort(key=lambda x: x[1].to_comparable(sorting))
        return [v[0] for v in videos]

    # =========================================================================
    # Index management
    # =========================================================================

    def _update_video_index(self, video_id: int, filename: str, data: dict):
        """Update search index for a single video."""
        from pysaurus.database.newsql.migration import (
            extract_flags_from_video_dict,
            extract_terms_from_video_dict,
        )

        # Get prop_types for term extraction
        prop_types = {pt["name"]: pt for pt in self._sql.get_prop_types()}

        # Extract terms and flags
        terms = extract_terms_from_video_dict(data, prop_types)
        flags = extract_flags_from_video_dict(data)

        # Update thumbnail flags
        has_thumb = self._sql.has_thumbnail(filename)
        flags["with_thumbnails"] = has_thumb
        flags["without_thumbnails"] = not has_thumb

        # Update discarded flag
        flags["discarded"] = self._is_discarded(AbsolutePath.ensure(filename))

        # Update index
        self._sql.remove_search_terms(filename)
        self._sql.remove_video_flags(filename)
        self._sql.add_search_terms(filename, terms)
        self._sql.set_video_flags(filename, flags)

    # =========================================================================
    # Save
    # =========================================================================

    def _save(self):
        """SQL database auto-commits, but we ensure WAL checkpoint."""
        self._sql.execute("PRAGMA wal_checkpoint(PASSIVE)")
