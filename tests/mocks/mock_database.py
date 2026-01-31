"""
Mock database for fast unit testing.

Provides in-memory implementation of database interfaces used by NiceGUI.
Loads test data from JSON, all operations happen in memory.
"""

import copy
import json
import random
from pathlib import Path
from typing import Any

from pysaurus.application import exceptions
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.classes import Selector
from pysaurus.video.video_search_context import VideoSearchContext
from pysaurus.video_provider.field_stat import FieldStat
from pysaurus.video_provider.view_tools import GroupDef, SearchDef


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


class MockProvider:
    """Mock implementation of video provider."""

    def __init__(self, database: "MockDatabase"):
        self._db = database
        self._sources: list[list[str]] = []
        self._grouping: GroupDef = GroupDef()
        self._search: SearchDef | None = None
        self._sorting: list[str] = []
        self._classifier_path: list[str] = []
        self._group_id: int = 0

    def _filter_videos(self) -> list[dict]:
        """Apply filters and return matching videos."""
        videos = self._db._videos

        # Apply search filter
        if self._search and self._search.text:
            text = self._search.text.lower()
            videos = [
                v
                for v in videos
                if text in v.get("meta_title", "").lower()
                or text in v.get("filename", "").lower()
            ]

        # Apply source filter
        if self._sources:
            filtered = []
            for v in videos:
                for source_path in self._sources:
                    if self._video_matches_source(v, source_path):
                        filtered.append(v)
                        break
            videos = filtered

        return videos

    def _video_matches_source(self, video: dict, source_path: list[str]) -> bool:
        """Check if video matches a source filter path."""
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

    def _sort_videos(self, videos: list[dict]) -> list[dict]:
        """Sort videos by current sorting configuration."""
        if not self._sorting:
            return videos

        result = videos.copy()
        for sort_key in reversed(self._sorting):
            reverse = sort_key.startswith("-")
            field = sort_key.lstrip("-")
            result.sort(key=lambda v: v.get(field, ""), reverse=reverse)
        return result

    def get_current_state(
        self, page_size: int, page_number: int, selector: Selector | None = None
    ) -> VideoSearchContext:
        """Get current view state."""
        from pysaurus.core.duration import Duration
        from pysaurus.core.file_size import FileSize

        # Filter and sort
        videos = self._filter_videos()
        videos = self._sort_videos(videos)

        # Compute stats
        total_count = len(videos)
        total_size = sum(v.get("file_size", 0) for v in videos)
        total_duration = sum(
            v.get("duration", 0) / (v.get("duration_time_base", 1) or 1)
            for v in videos
        )

        # Pagination
        nb_pages = max(1, (total_count + page_size - 1) // page_size)
        start = page_number * page_size
        end = start + page_size
        page_videos = videos[start:end]

        # Convert to MockVideoPattern
        result = [MockVideoPattern(v) for v in page_videos]

        # Build classifier stats if grouping
        classifier_stats = []
        if self._grouping and self._grouping.field:
            stats = self._compute_group_stats(videos)
            classifier_stats = [
                FieldStat(
                    is_property=self._grouping.is_property, value=value, count=count
                )
                for value, count in stats.items()
            ]

        return VideoSearchContext(
            sources=self._sources or None,
            grouping=self._grouping,
            classifier=self._classifier_path or None,
            group_id=self._group_id,
            search=self._search,
            sorting=self._sorting or None,
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
            source_count=len(self._db._videos),
        )

    def _compute_group_stats(self, videos: list[dict]) -> dict[Any, int]:
        """Compute group statistics for current grouping."""
        stats = {}
        field = self._grouping.field
        is_property = self._grouping.is_property

        for v in videos:
            if is_property:
                values = v.get("properties", {}).get(field, [])
            else:
                values = [v.get(field)]

            for val in values:
                if val is not None:
                    stats[val] = stats.get(val, 0) + 1

        return stats

    def set_sources(self, paths: list[list[str]]) -> None:
        """Set source filter."""
        self._sources = paths

    def set_groups(
        self,
        field: str,
        is_property: bool = False,
        sorting: str = "field",
        reverse: bool = False,
        allow_singletons: bool = True,
    ) -> None:
        """Set grouping configuration."""
        self._grouping = GroupDef(
            field=field,
            is_property=is_property,
            sorting=sorting,
            reverse=reverse,
            allow_singletons=allow_singletons,
        )

    def set_search(self, text: str, cond: str = "and") -> None:
        """Set search filter."""
        self._search = SearchDef(text=text, cond=cond) if text else None

    def set_sort(self, sorting: list[str]) -> None:
        """Set sorting configuration."""
        self._sorting = sorting or []

    def classifier_select_group(self, group_id: int) -> None:
        """Select a group in classifier mode."""
        self._group_id = group_id

    def classifier_back(self) -> None:
        """Go back in classifier path."""
        if self._classifier_path:
            self._classifier_path.pop()

    def classifier_reverse(self) -> None:
        """Reverse classifier path."""
        self._classifier_path.reverse()

    def choose_random_video(self) -> int:
        """Choose a random video ID."""
        videos = self._filter_videos()
        if videos:
            return random.choice(videos)["video_id"]
        return 0

    def apply_on_view(
        self, selector: dict, fn_name: str, *fn_args
    ) -> dict[str, Any]:
        """Apply a function on selected videos."""
        # Mock implementation - just return success
        return {"applied": True, "fn_name": fn_name}

    def get_classifier_path(self) -> list[str]:
        """Get current classifier path."""
        return self._classifier_path

    def get_grouping(self) -> GroupDef:
        """Get current grouping definition."""
        return self._grouping

    def set_classifier_path(self, path: list[str]) -> None:
        """Set classifier path."""
        self._classifier_path = path

    def set_group(self, group_id: int) -> None:
        """Set current group ID."""
        self._group_id = group_id

    def get_view_indices(self) -> list[int]:
        """Get video IDs in current view."""
        videos = self._filter_videos()
        return [v["video_id"] for v in videos]

    def refresh(self) -> None:
        """Refresh the provider state."""
        pass


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

    def apply_on_prop_value(
        self, prop_name: str, prop_value: Any, fn_name: str, *fn_args
    ) -> None:
        """Apply function on property value."""
        pass

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

        self.provider = MockProvider(self)
        self.ops = MockOps(self)
        self.algos = self  # Self-reference for algos.refresh()
        self.notifier = None

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
        """Get property types."""
        return self._prop_types

    def get_videos(
        self,
        include: list[str] | None = None,
        where: dict | None = None,
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
        self,
        name: str,
        prop_type: str,
        definition: Any = None,
        multiple: bool = False,
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

    def refresh(self) -> None:
        """Refresh database (no-op for mock)."""
        pass

    @classmethod
    def create_fresh(cls) -> "MockDatabase":
        """Create a fresh copy of mock database."""
        return cls(load_test_data())