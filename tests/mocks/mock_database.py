"""
Mock database for fast unit testing.

Provides in-memory implementation of database interfaces for testing.
Loads test data from JSON, all operations happen in memory.
"""

import copy
import json
from pathlib import Path
from typing import Any

from pysaurus.application import exceptions
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.video.video_search_context import VideoSearchContext
from pysaurus.dbview.field_stat import FieldStat
from pysaurus.dbview.view_tools import GroupDef


# Load test data
TEST_DATA_PATH = Path(__file__).parent / "test_data.json"


def load_test_data() -> dict:
    """Load test data from JSON file."""
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


class MockVideoPattern:
    """Mock implementation of VideoPattern for testing."""

    __slots__ = ("_data",)

    def __init__(self, data: dict):
        self._data = data

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._data.get(name)

    @property
    def filename(self) -> AbsolutePath:
        return AbsolutePath(self._data["filename"])

    @property
    def file_size(self) -> int:
        return self._data["file_size"]

    @property
    def video_id(self) -> int:
        return self._data["video_id"]

    @property
    def errors(self) -> list[str]:
        return self._data.get("errors", [])

    @property
    def mtime(self) -> float:
        return self._data["mtime"]

    @property
    def extension(self) -> str:
        return self.filename.extension

    @property
    def file_title(self) -> str:
        return self.filename.file_title

    @property
    def title(self) -> str:
        return self._data.get("meta_title") or self.file_title

    @property
    def readable(self) -> bool:
        return not self._data.get("unreadable", False)

    @property
    def not_found(self) -> bool:
        return not self._data.get("found", True)

    @property
    def without_thumbnails(self) -> bool:
        return not self._data.get("with_thumbnails", False)

    @property
    def thumbnail(self) -> bytes:
        return b""

    @property
    def thumbnail_base64(self) -> str | None:
        return None

    @property
    def thumbnail_path(self) -> str | None:
        return None

    @property
    def properties(self) -> dict[str, list]:
        return self._data.get("properties", {})

    @property
    def moves(self) -> list:
        return self._data.get("moves", [])

    def get_property(self, name: str, default=None):
        """Get a property value by name."""
        props = self.properties
        if name in props:
            values = props[name]
            if isinstance(values, list):
                return values if len(values) > 1 else (values[0] if values else default)
            return values
        return default

    def json(self, with_moves=False) -> dict:
        """Return video as dict for JSON serialization."""
        from pysaurus.core.duration import Duration
        from pysaurus.core.file_size import FileSize

        d = self._data
        filename = self.filename
        file_title = filename.file_title
        title = d.get("meta_title") or file_title

        duration = d.get("duration", 0)
        duration_time_base = d.get("duration_time_base", 1) or 1
        file_size = d.get("file_size", 0)

        # Calculate bit_rate
        bit_rate = FileSize(
            file_size * duration_time_base / duration if duration else 0
        )
        length = Duration(duration * 1000000 / duration_time_base)
        size = FileSize(file_size)

        return {
            "audio_bit_rate": d.get("audio_bit_rate", 0),
            "audio_bits": d.get("audio_bits", 0),
            "audio_codec": str(d.get("audio_codec", "")),
            "audio_codec_description": str(d.get("audio_codec_description", "")),
            "audio_languages": d.get("audio_languages", []),
            "bit_depth": d.get("bit_depth", 0),
            "bit_rate": str(bit_rate),
            "channels": d.get("channels", 0),
            "container_format": str(d.get("container_format", "")),
            "date": d.get("date_entry_modified", ""),
            "date_entry_modified": str(d.get("date_entry_modified", "")),
            "date_entry_opened": str(d.get("date_entry_opened", "")),
            "errors": list(d.get("errors", [])),
            "extension": filename.extension,
            "file_size": file_size,
            "file_title": file_title,
            "filename": filename.standard_path,
            "found": d.get("found", True),
            "frame_rate": (
                d.get("frame_rate_num", 0) / (d.get("frame_rate_den", 1) or 1)
            ),
            "height": d.get("height", 0),
            "length": str(length),
            "moves": self.moves if with_moves else None,
            "properties": self.properties,
            "readable": not d.get("unreadable", False),
            "sample_rate": d.get("sample_rate", 0),
            "similarity_id": d.get("similarity_id"),
            "size": str(size),
            "subtitle_languages": d.get("subtitle_languages", []),
            "thumbnail_path": self.thumbnail_path,
            "thumbnail_base64": self.thumbnail_base64,
            "title": title,
            "video_codec": str(d.get("video_codec", "")),
            "video_codec_description": str(d.get("video_codec_description", "")),
            "video_id": d["video_id"],
            "width": d.get("width", 0),
            "with_thumbnails": d.get("with_thumbnails", False),
            "watched": d.get("watched", False),
        }


class MockOps:
    """Mock implementation of database operations."""

    def __init__(self, database: "MockDatabase"):
        self._db = database

    def open_video(self, video_id: int) -> str:
        """Open a video file."""
        video = self._db._get_video(video_id)
        if video:
            return video["filename"]
        raise ValueError(f"Video not found: {video_id}")

    def mark_as_read(self, video_id: int) -> bool:
        """Toggle video watched status."""
        video = self._db._get_video(video_id)
        if video:
            video["watched"] = not video.get("watched", False)
            return True
        return False

    def mark_as_watched(self, video_id: int) -> bool:
        """Mark video as watched."""
        video = self._db._get_video(video_id)
        if video:
            video["watched"] = True
            return True
        return False

    def delete_video(self, video_id: int) -> bool:
        """Delete a video."""
        for i, v in enumerate(self._db._videos):
            if v["video_id"] == video_id:
                self._db._videos.pop(i)
                return True
        return False

    def change_video_file_title(self, video_id: int, new_title: str) -> str:
        """Change video file title."""
        video = self._db._get_video(video_id)
        if video:
            video["meta_title"] = new_title
            return video["filename"]
        raise ValueError(f"Video not found: {video_id}")

    def get_video_filename(self, video_id: int) -> AbsolutePath:
        """Get video filename."""
        video = self._db._get_video(video_id)
        if video:
            return AbsolutePath(video["filename"])
        raise ValueError(f"Video not found: {video_id}")

    def set_similarities_from_list(self, similarities: list) -> None:
        """Set similarity IDs from list."""
        pass

    def apply_on_prop_value(self, prop_name: str, mod_name: str) -> None:
        """Apply a modifier function to property values."""
        from pysaurus.database.property_value_modifier import PropertyValueModifier

        function = getattr(PropertyValueModifier(), mod_name)
        for v in self._db._videos:
            props = v.get("properties", {})
            if prop_name in props:
                old_values = props[prop_name]
                new_values = [function(value) for value in old_values]
                if old_values and new_values != old_values:
                    props[prop_name] = new_values

    def move_video_entry(self, video_id: int, new_path: str) -> bool:
        """Move video entry to new path."""
        video = self._db._get_video(video_id)
        if video:
            video["filename"] = new_path
            return True
        return False

    def set_folders(self, video_id: int, folders: list[str]) -> None:
        """Set video folders."""
        pass


class MockDatabase:
    """
    Mock database for fast unit testing.

    Loads data from JSON and keeps everything in memory.
    No disk I/O during tests.
    """

    def __init__(self, data: dict | None = None):
        """Initialize mock database."""
        if data is None:
            data = load_test_data()

        self._name = data["name"]
        self._folders = [AbsolutePath(f) for f in data["folders"]]
        self._prop_types = copy.deepcopy(data["prop_types"])
        self._videos = copy.deepcopy(data["videos"])

        self.ops = MockOps(self)
        self.algos = self  # Self-reference for algos.refresh()
        self.notifier = None
        self.in_save_context = False

    def query_videos(self, view, page_size, page_number, selector=None):
        """Query videos with filtering, sorting and pagination."""
        from pysaurus.core.duration import Duration
        from pysaurus.core.file_size import FileSize

        videos = self._filter_videos(view.sources, view.search)
        videos = self._sort_videos(videos, view.sorting)

        total_count = len(videos)
        total_size = sum(v.get("file_size", 0) for v in videos)
        total_duration = sum(
            v.get("duration", 0) / (v.get("duration_time_base", 1) or 1) for v in videos
        )

        if page_size and page_number is not None:
            nb_pages = max(1, (total_count + page_size - 1) // page_size)
            start = page_number * page_size
            page_videos = videos[start : start + page_size]
        else:
            nb_pages = 1
            page_videos = videos

        result = [MockVideoPattern(v) for v in page_videos]

        classifier_stats = []
        grouping = view.grouping
        if grouping and grouping.field:
            stats = self._compute_group_stats(videos, grouping)
            classifier_stats = [
                FieldStat(is_property=grouping.is_property, value=value, count=count)
                for value, count in stats.items()
            ]

        return VideoSearchContext(
            sources=view.sources or None,
            grouping=grouping,
            classifier=view.classifier or None,
            group_id=view.group,
            search=view.search,
            sorting=view.sorting or None,
            selector=selector,
            page_size=page_size,
            page_number=page_number,
            with_moves=False,
            result=result,
            nb_pages=nb_pages,
            view_count=total_count,
            selection_count=total_count,
            selection_duration=Duration(total_duration * 1000000),
            selection_file_size=FileSize(total_size),
            classifier_stats=classifier_stats,
            source_count=len(self._videos),
        )

    def _filter_videos(self, sources, search) -> list[dict]:
        """Filter videos by sources and search."""
        videos = self._videos

        if search and search.text:
            text = search.text.lower()
            videos = [
                v
                for v in videos
                if text in v.get("meta_title", "").lower()
                or text in v.get("filename", "").lower()
            ]

        if sources:
            filtered = []
            for v in videos:
                for source_path in sources:
                    if self._video_matches_source(v, source_path):
                        filtered.append(v)
                        break
            videos = filtered

        return videos

    @staticmethod
    def _video_matches_source(video: dict, source_path: list[str]) -> bool:
        for part in source_path:
            if part == "readable" and video.get("unreadable", False):
                return False
            if part == "unreadable" and not video.get("unreadable", False):
                return False
            if part == "found" and not video.get("found", True):
                return False
            if part == "not_found" and video.get("found", True):
                return False
        return True

    @staticmethod
    def _sort_videos(videos: list[dict], sorting: list[str]) -> list[dict]:
        if not sorting:
            return videos
        result = videos.copy()
        for sort_key in reversed(sorting):
            reverse = sort_key.startswith("-")
            field = sort_key.lstrip("-")
            result.sort(key=lambda v: v.get(field, ""), reverse=reverse)
        return result

    @staticmethod
    def _compute_group_stats(videos: list[dict], grouping: GroupDef) -> dict[Any, int]:
        stats = {}
        for v in videos:
            if grouping.is_property:
                values = v.get("properties", {}).get(grouping.field, [])
            else:
                values = [v.get(grouping.field)]
            for val in values:
                if val is not None:
                    stats[val] = stats.get(val, 0) + 1
        return stats

    def apply_on_view(self, selector: dict, fn_name: str, *fn_args):
        """Apply a function on selected videos."""
        all_ids = [v["video_id"] for v in self._videos]

        if not selector:
            video_ids = all_ids
        elif "all" in selector:
            is_all = selector.get("all", False)
            include = set(selector.get("include", []))
            exclude = set(selector.get("exclude", []))
            if is_all:
                video_ids = [vid for vid in all_ids if vid not in exclude]
            else:
                video_ids = [vid for vid in all_ids if vid in include]
        else:
            mode = selector.get("mode", "include")
            selection = set(selector.get("selection", []))
            if mode == "include":
                video_ids = [vid for vid in all_ids if vid in selection]
            else:
                video_ids = [vid for vid in all_ids if vid not in selection]

        if fn_name == "count_property_values":
            prop_name = fn_args[0] if fn_args else None
            value_counts: dict[Any, int] = {}
            for video in self._videos:
                if video["video_id"] in video_ids:
                    for val in video.get("properties", {}).get(prop_name, []):
                        value_counts[val] = value_counts.get(val, 0) + 1
            return [[val, count] for val, count in value_counts.items()]

        elif fn_name == "edit_property_for_videos":
            prop_name = fn_args[0] if len(fn_args) > 0 else None
            to_add = fn_args[1] if len(fn_args) > 1 else []
            to_remove = fn_args[2] if len(fn_args) > 2 else []
            modified = 0
            for video in self._videos:
                if video["video_id"] in video_ids:
                    props = video.setdefault("properties", {})
                    values = list(props.get(prop_name, []))
                    original = list(values)
                    for val in to_remove:
                        if val in values:
                            values.remove(val)
                    for val in to_add:
                        if val not in values:
                            values.append(val)
                    if values != original:
                        props[prop_name] = values
                        modified += 1
            return modified

        return {"applied": True, "fn_name": fn_name}

    def _get_video(self, video_id: int) -> dict | None:
        """Get video by ID."""
        for v in self._videos:
            if v["video_id"] == video_id:
                return v
        return None

    def get_name(self) -> str:
        """Get database name."""
        return self._name

    def get_folders(self) -> list[AbsolutePath]:
        """Get database folders."""
        return self._folders

    def get_prop_types(self) -> list[dict]:
        """Get property types in flat format for PySide6 interface."""
        result = []
        for pt in self._prop_types:
            # Flatten the definition into the prop_type dict
            definition = pt.get("definition", {})
            flat_pt = {
                "name": pt["name"],
                "type": definition.get("type", "str"),
                "multiple": pt.get("multiple", False),
                "enumeration": definition.get("enumeration"),
                "defaultValues": definition.get("defaultValues", []),
            }
            result.append(flat_pt)
        return result

    def get_videos(
        self, include: list[str] | None = None, where: dict | None = None
    ) -> list[MockVideoPattern]:
        """Get videos with optional filtering."""
        videos = self._videos

        if where:
            filtered = []
            for v in videos:
                match = True
                for key, value in where.items():
                    if v.get(key) != value:
                        match = False
                        break
                if match:
                    filtered.append(v)
            videos = filtered

        return [MockVideoPattern(v) for v in videos]

    def videos_tag_get(
        self, prop_name: str, indices: list[int] | None = None
    ) -> dict[int, list]:
        """Get property values for videos."""
        result = {}
        for v in self._videos:
            if indices is None or v["video_id"] in indices:
                props = v.get("properties", {})
                if prop_name in props:
                    result[v["video_id"]] = props[prop_name]
        return result

    def rename(self, new_name: str) -> None:
        """Rename database."""
        self._name = new_name

    def prop_type_add(
        self, name: str, prop_type: str, definition: Any = None, multiple: bool = False
    ) -> None:
        """Add a new property type."""
        # Check if already exists
        for pt in self._prop_types:
            if pt["name"] == name:
                raise exceptions.PropertyAlreadyExists(name)

        self._prop_types.append(
            {
                "name": name,
                "definition": {
                    "type": prop_type,
                    "enumeration": definition if isinstance(definition, list) else None,
                    "defaultValues": (
                        [definition]
                        if definition and not isinstance(definition, list)
                        else []
                    ),
                },
                "multiple": multiple,
            }
        )

    def prop_type_del(self, name: str) -> None:
        """Delete a property type."""
        for i, pt in enumerate(self._prop_types):
            if pt["name"] == name:
                self._prop_types.pop(i)
                # Remove from all videos
                for v in self._videos:
                    if "properties" in v and name in v["properties"]:
                        del v["properties"][name]
                return
        raise exceptions.PropertyNotFound(name)

    def prop_type_set_name(self, old_name: str, new_name: str) -> None:
        """Rename a property type."""
        for pt in self._prop_types:
            if pt["name"] == old_name:
                pt["name"] = new_name
                # Rename in all videos
                for v in self._videos:
                    if "properties" in v and old_name in v["properties"]:
                        v["properties"][new_name] = v["properties"].pop(old_name)
                return
        raise exceptions.PropertyNotFound(old_name)

    def prop_type_set_multiple(self, name: str, multiple: bool) -> None:
        """Set property multiplicity."""
        for pt in self._prop_types:
            if pt["name"] == name:
                pt["multiple"] = multiple
                return
        raise exceptions.PropertyNotFound(name)

    def video_entry_del(self, video_id: int) -> bool:
        """Delete a video entry."""
        for i, v in enumerate(self._videos):
            if v["video_id"] == video_id:
                self._videos.pop(i)
                return True
        return False

    def video_entry_set_tags(self, video_id: int, properties: dict[str, Any]) -> None:
        """Set properties for a video."""
        video = self._get_video(video_id)
        if video:
            if "properties" not in video:
                video["properties"] = {}
            for name, values in properties.items():
                if isinstance(values, list):
                    video["properties"][name] = values
                else:
                    video["properties"][name] = [values]

    def video_entry_set_filename(self, video_id: int, new_path: str) -> str | None:
        """Set video filename."""
        video = self._get_video(video_id)
        if video:
            old_path = video["filename"]
            video["filename"] = str(new_path)
            return old_path
        return None

    def delete_property_values(self, name: str, values: list) -> None:
        """Delete property values across all videos."""
        values_set = set(values)
        for v in self._videos:
            props = v.get("properties", {})
            if name in props:
                props[name] = [val for val in props[name] if val not in values_set]
                if not props[name]:
                    del props[name]

    def replace_property_values(
        self, name: str, old_values: list, new_value: object
    ) -> bool:
        """Replace property values across all videos."""
        old_set = set(old_values)
        modified = False
        for v in self._videos:
            props = v.get("properties", {})
            if name in props:
                current = set(props[name])
                removed = current & old_set
                if removed:
                    next_values = (current - old_set) | {new_value}
                    props[name] = sorted(next_values)
                    modified = True
        return modified

    def refresh(self) -> None:
        """Refresh database (no-op for mock)."""
        pass

    @classmethod
    def create_fresh(cls) -> "MockDatabase":
        """Create a fresh copy of mock database."""
        return cls(load_test_data())
