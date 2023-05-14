"""
Video class. Properties:

- length: Return a Duration object representing the video duration.
  Based on raw duration fields `duration` and `duration_time_base`, we have: ::

    duration = (number of seconds) * duration_time_base

  So: ::

    (number of seconds) = duration / duration_time_base
"""
from typing import Any, Dict, Iterable, List, Set

from other.toolsaurus.jsonable import Jsonable
from other.toolsaurus.other_video.video_runtime_info import VideoRuntimeInfo
from pysaurus.core.classes import StringPrinter, StringedTuple, Text
from pysaurus.core.compare import to_comparable
from pysaurus.core.components import AbsolutePath, Date, Duration, FileSize
from pysaurus.core.constants import JPEG_EXTENSION, PYTHON_ERROR_THUMBNAIL
from pysaurus.core.functions import (
    class_get_public_attributes,
    html_to_title,
    string_to_pieces,
)
from pysaurus.core.modules import FNV64
from pysaurus.core.semantic_text import SemanticText
from pysaurus.video.video_sorting import VideoSorting


class Video(Jsonable):
    filename: ("f", str) = None
    file_size: "s" = 0
    errors: "e" = set()
    video_id: ("j", int) = None
    runtime: ("R", VideoRuntimeInfo) = {}
    thumb_name: "i" = ""
    date_entry_modified: ("m", float) = None
    date_entry_opened: ("o", float) = None

    unreadable: "U" = False
    audio_bit_rate: "r" = 0
    audio_codec: "a" = ""
    audio_codec_description: "A" = ""
    bit_depth: "D" = 0
    channels: "C" = 2
    container_format: "c" = ""
    device_name: "b" = ""
    duration: "d" = 0.0
    duration_time_base: "t" = 0
    frame_rate_den: "y" = 0
    frame_rate_num: "x" = 0
    height: "h" = 0
    meta_title: "n" = ""
    properties: "p" = {}
    sample_rate: "u" = 0
    similarity_id: ("S", int) = None
    video_codec: "v" = ""
    video_codec_description: "V" = ""
    width: "w" = 0
    audio_languages: "l" = []
    subtitle_languages: "L" = []

    __slots__ = ("discarded", "database")
    __protected__ = ("database", "runtime", "discarded")
    FLAGS = {
        "readable",
        "unreadable",
        "found",
        "not_found",
        "with_thumbnails",
        "without_thumbnails",
    }

    def __init__(self, database, **kwargs):
        super().__init__(**kwargs)
        self.__json__["duration"] = abs(self.__json__["duration"])
        self.__json__["duration_time_base"] = self.__json__["duration_time_base"] or 1
        self.__json__["frame_rate_den"] = self.__json__["frame_rate_den"] or 1
        # Runtime
        self.discarded = False
        self.database = database

    def __str__(self):
        cls = type(self)
        with StringPrinter() as printer:
            printer.write(f"{cls.__name__} {self.video_id}:")
            for field in class_get_public_attributes(cls):
                printer.write(f"\t{field}: {getattr(self, field)}")
            return str(printer)

    def __hash__(self):
        return hash(self.filename)

    def __eq__(self, other):
        return self.filename == other.filename

    def __lt__(self, other):
        return self.filename < other.filename

    def _get_filename(self):
        return AbsolutePath(self.__json__["filename"])

    def _set_filename(self, data):
        assert isinstance(data, (str, AbsolutePath))
        self.__json__["filename"] = str(data)
        self._save_date_entry_modified()

    def _get_audio_codec(self):
        return Text(self.__json__["audio_codec"])

    def _get_audio_codec_description(self):
        return Text(self.__json__["audio_codec_description"])

    def _get_container_format(self):
        return Text(self.__json__["container_format"])

    def _get_device_name(self):
        return Text(self.__json__["device_name"])

    def _get_meta_title(self):
        return Text(html_to_title(self.__json__["meta_title"]))

    def _get_video_codec(self):
        return Text(self.__json__["video_codec"])

    def _get_video_codec_description(self):
        return Text(self.__json__["video_codec_description"])

    def _get_thumb_name(self):
        if not self.__json__["thumb_name"]:
            self.__json__["thumb_name"] = FNV64.hash(self.filename.standard_path)
        return self.__json__["thumb_name"]

    def _get_date_entry_modified(self):
        if self.__json__["date_entry_modified"] is None:
            self.__json__["date_entry_modified"] = self.runtime.mtime
        return Date(self.__json__["date_entry_modified"])

    def _get_date_entry_opened(self):
        if self.__json__["date_entry_opened"] is None:
            self.__json__["date_entry_opened"] = self.runtime.mtime
        return Date(self.__json__["date_entry_opened"])

    def _set_properties(self, properties: dict):
        raise NotImplementedError()

    def _set_similarity_id(self, data):
        if self.__json__["similarity_id"] != data:
            self.__json__["similarity_id"] = data
            self._save_date_entry_modified()

    def _to_dict_errors(self, errors):
        return list(errors)

    @classmethod
    def _from_dict_errors(cls, errors):
        return set(errors)

    # Not implemented in LazyVideo
    def extract_attributes(self, keys: Iterable[str]) -> Dict[str, Any]:
        out = {}
        for key in keys:
            if key.startswith(":"):
                prop_name = key[1:]
                out.setdefault("properties", {})[prop_name] = self.get_property(
                    prop_name
                )
            else:
                out[key] = getattr(self, key)
        return out

    extension = property(lambda self: self.filename.extension)
    file_title = property(lambda self: Text(self.filename.file_title))
    file_title_numeric = property(lambda self: SemanticText(self.filename.file_title))
    size = property(lambda self: FileSize(self.file_size))
    day = property(lambda self: self.date.day)
    # runtime attributes
    disk = property(
        lambda self: self.filename.get_drive_name() or self.runtime.driver_id
    )
    date = property(lambda self: Date(self.runtime.mtime))

    readable = property(lambda self: not self.unreadable)
    found = property(lambda self: self.runtime.is_file)
    not_found = property(lambda self: not self.runtime.is_file)
    with_thumbnails = property(
        lambda self: not self.unreadable_thumbnail and self.runtime.has_thumbnail
    )
    without_thumbnails = property(lambda self: not self.with_thumbnails)

    frame_rate = property(lambda self: self.frame_rate_num / self.frame_rate_den)
    length = property(
        lambda self: Duration(round(self.duration * 1000000 / self.duration_time_base))
    )
    title = property(
        lambda self: self.meta_title
        if self.meta_title
        else Text(self.filename.file_title)
    )
    title_numeric = property(
        lambda self: self.meta_title_numeric
        if self.meta_title
        else self.file_title_numeric
    )
    filename_numeric = property(lambda self: SemanticText(self.filename.standard_path))
    meta_title_numeric = property(lambda self: SemanticText(self.meta_title.value))
    raw_seconds = property(lambda self: self.duration / self.duration_time_base)
    raw_microseconds = property(
        lambda self: self.duration * 1000000 / self.duration_time_base
    )
    thumbnail_path = property(
        lambda self: AbsolutePath.file_path(
            self.database.thumbnail_folder, self.thumb_name, JPEG_EXTENSION
        )
    )
    move_id = property(lambda self: self.database.moves_attribute(self)[0])
    size_length = property(lambda self: StringedTuple((self.size, self.length)))

    @property
    def unreadable_thumbnail(self):
        return PYTHON_ERROR_THUMBNAIL in self.errors

    @unreadable_thumbnail.setter
    def unreadable_thumbnail(self, has_error):
        if has_error:
            self.errors.add(PYTHON_ERROR_THUMBNAIL)
        elif PYTHON_ERROR_THUMBNAIL in self.errors:
            self.errors.remove(PYTHON_ERROR_THUMBNAIL)

    @property
    def quality_compression(self):
        if self.unreadable:
            return 0
        basic_file_size = (
            self.width * self.height * self.frame_rate * 3
            + self.sample_rate * self.channels * 2
            # todo: why x 2 ?
        ) * self.raw_seconds
        return self.file_size / basic_file_size

    @property
    def moves(self):
        return [
            {"video_id": video.video_id, "filename": video.filename}
            for video in self.database.moves_attribute(self)[1]
        ]

    @property
    def has_runtime_thumbnail(self):
        return self.runtime.has_thumbnail

    @has_runtime_thumbnail.setter
    def has_runtime_thumbnail(self, value: bool):
        self.runtime.has_thumbnail = bool(value)

    def terms(self) -> List[str]:
        term_sources = [self.filename.path, str(self.meta_title)]
        for name, val in self.properties.items():
            if self.database.has_prop_type(name, with_type=str):
                if isinstance(val, list):
                    term_sources.extend(val)
                else:
                    term_sources.append(val)
        all_str = " ".join(term_sources)
        t_all_str = string_to_pieces(all_str)
        t_all_str_low = string_to_pieces(all_str.lower())
        return t_all_str if t_all_str == t_all_str_low else (t_all_str + t_all_str_low)

    def to_comparable(self, sorting: VideoSorting) -> list:
        return [
            to_comparable(getattr(self, field), reverse) for field, reverse in sorting
        ]

    def has_property(self, name):
        return name in self.properties

    def get_property(self, name, *default):
        return self.properties.get(name, *default) if default else self.properties[name]

    def remove_property(self, name, *default):
        self._save_date_entry_modified()
        return self.properties.pop(name, *default)

    def set_properties(self, properties: Dict[str, Any]) -> Set[str]:
        return {
            name for name, value in properties.items() if self.set_property(name, value)
        }

    def set_property(self, name, value) -> bool:
        modified = False
        if value is None:
            if name in self.properties:
                modified = True
                del self.properties[name]
        else:
            if name not in self.properties or self.properties[name] != value:
                modified = True
            self.properties[name] = value
        if modified:
            self._save_date_entry_modified()
        return modified

    def open(self):
        self.filename.open()
        self.date_entry_opened = Date.now().time

    def _save_date_entry_modified(self):
        self.date_entry_modified = Date.now().time
