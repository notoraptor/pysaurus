import base64
from typing import Any, List, Tuple

from pysaurus.core.classes import StringedTuple
from pysaurus.core.components import AbsolutePath, Date, Duration, FileSize
from saurus.sql.sql_old.video_entry import VIDEO_TABLE_FIELDS

VIDEO_TABLE_FIELD_SET = set(VIDEO_TABLE_FIELDS)


def assert_video_table_field(value: str) -> str:
    assert value in VIDEO_TABLE_FIELD_SET
    return value


class VideoParser:
    __slots__ = ()

    def __call__(self, field, value) -> Tuple[str, Any]:
        return (
            getattr(self, field)(value)
            if hasattr(self, field)
            else (assert_video_table_field(field), value)
        )

    @classmethod
    def video_id(cls, value) -> Tuple[str, List[int]]:
        return "video_id", (
            value
            if isinstance(value, list)
            else list(value)
            if isinstance(value, (tuple, set))
            else [value]
        )

    @classmethod
    def filename(cls, value) -> Tuple[str, List[AbsolutePath]]:
        if not isinstance(value, (list, tuple, set)):
            value = [value]
        return "filename", [AbsolutePath.ensure(el).path for el in value]

    @classmethod
    def date_entry_modified(cls, value) -> Tuple[str, float]:
        return "date_entry_modified", float(value)

    @classmethod
    def date_entry_opened(cls, value) -> Tuple[str, float]:
        return "date_entry_opened", float(value)

    @classmethod
    def readable(cls, value) -> Tuple[str, int]:
        return "unreadable", int(not value)

    @classmethod
    def found(cls, value) -> Tuple[str, int]:
        return "is_file", value

    @classmethod
    def not_found(cls, value) -> Tuple[str, int]:
        return "is_file", int(not value)

    @classmethod
    def without_thumbnails(cls, value) -> Tuple[str, int]:
        return "with_thumbnails", int(not value)


class SQLVideoWrapper:
    __slots__ = (
        "data",
        "audio_languages",
        "subtitle_languages",
        "errors",
        "json_properties",
        "moves",
    )

    def __init__(
        self,
        data: dict,
        audio_languages=[],
        subtitle_languages=[],
        errors=[],
        json_properties={},
        moves=[],
    ):
        # Data must contains key "with_thumbnails"
        self.data = data
        self.audio_languages = audio_languages
        self.subtitle_languages = subtitle_languages
        self.errors = errors
        self.json_properties = json_properties
        self.moves = moves  # list of dicts {video_id => int, filename => str}

    @property
    def filename(self) -> AbsolutePath:
        return AbsolutePath(self.data["filename"])

    @property
    def video_id(self):
        return self.data["video_id"]

    @property
    def file_size(self):
        return self.data["file_size"]

    @property
    def unreadable(self):
        return self.data["unreadable"]

    @property
    def audio_bit_rate(self):
        return self.data["audio_bit_rate"]

    @property
    def audio_bits(self):
        return self.data["audio_bits"]

    @property
    def audio_codec(self):
        return self.data["audio_codec"]

    @property
    def audio_codec_description(self):
        return self.data["audio_codec_description"]

    @property
    def bit_depth(self):
        return self.data["bit_depth"]

    @property
    def channels(self):
        return self.data["channels"]

    @property
    def container_format(self):
        return self.data["container_format"]

    @property
    def device_name(self):
        return self.data["device_name"]

    @property
    def duration(self):
        return abs(self.data["duration"])

    @property
    def duration_time_base(self):
        return self.data["duration_time_base"] or 1

    @property
    def frame_rate_den(self):
        return self.data["frame_rate_den"] or 1

    @property
    def frame_rate_num(self):
        return self.data["frame_rate_num"]

    @property
    def height(self):
        return self.data["height"]

    @property
    def meta_title(self):
        return self.data["meta_title"]

    @property
    def sample_rate(self):
        return self.data["sample_rate"]

    @property
    def video_codec(self):
        return self.data["video_codec"]

    @property
    def video_codec_description(self):
        return self.data["video_codec_description"]

    @property
    def width(self):
        return self.data["width"]

    @property
    def mtime(self):
        return self.data["mtime"]

    @property
    def driver_id(self):
        return self.data["driver_id"]

    @property
    def is_file(self):
        return self.data["is_file"]

    @property
    def discarded(self):
        return self.data["discarded"]

    @property
    def date_entry_modified(self) -> Date:
        value = self.data["date_entry_modified"]
        return Date(value if value is not None else self.mtime)

    @property
    def date_entry_opened(self) -> Date:
        value = self.data["date_entry_opened"]
        return Date(value if value is not None else self.mtime)

    @property
    def similarity_id(self):
        return self.data["similarity_id"]

    # derived

    @property
    def found(self):
        return self.data["is_file"]

    @property
    def with_thumbnails(self):
        return self.data["with_thumbnails"]

    @property
    def extension(self):
        return self.filename.extension

    @property
    def file_title(self):
        return self.filename.file_title

    @property
    def file_title_numeric(self):
        return self.filename.file_title

    @property
    def size(self):
        return FileSize(self.file_size)

    @property
    def day(self):
        return self.date.day

    @property
    def disk(self):
        return self.filename.get_drive_name() or self.driver_id

    @property
    def date(self) -> Date:
        return Date(self.mtime)

    @property
    def readable(self):
        return not self.unreadable

    @property
    def not_found(self):
        return not self.found

    @property
    def without_thumbnails(self):
        return not self.with_thumbnails

    @property
    def frame_rate(self):
        return self.frame_rate_num / self.frame_rate_den

    @property
    def length(self):
        return Duration(round(self.duration * 1000000 / self.duration_time_base))

    @property
    def title(self):
        return self.meta_title or self.filename.file_title

    @property
    def title_numeric(self):
        return self.meta_title_numeric if self.meta_title else self.file_title_numeric

    @property
    def filename_numeric(self):
        return self.filename.standard_path

    @property
    def meta_title_numeric(self):
        return self.meta_title

    @property
    def raw_microseconds(self):
        return self.duration * 1000000 / self.duration_time_base

    @property
    def thumbnail_base64(self):
        data: bytes = self.data["thumbnail"]
        return (
            ("data:image/jpeg;base64," + base64.b64encode(data).decode())
            if data
            else None
        )

    @property
    def thumbnail_blob(self):
        return self.data.get("thumbnail")

    @property
    def size_length(self):
        return StringedTuple((self.size, self.length))

    @property
    def filename_length(self):
        return len(self.filename)

    @property
    def bit_rate(self):
        return FileSize(
            self.file_size * self.duration_time_base / self.duration
            if self.duration
            else 0
        )

    @property
    def move_id(self):
        return f"{self.size}, {self.length}"

    def json(self, with_moves=False) -> dict:
        return {
            "audio_bit_rate": self.data["audio_bit_rate"],
            "audio_bits": self.data["audio_bits"],
            "audio_codec": self.data["audio_codec"],
            "audio_codec_description": self.data["audio_codec_description"],
            "audio_languages": self.audio_languages,
            "bit_depth": self.data["bit_depth"],
            "bit_rate": str(self.bit_rate),
            "channels": self.data["channels"],
            "container_format": self.data["container_format"],
            "date": str(self.date),
            "date_entry_modified": str(self.date_entry_modified),
            "date_entry_opened": str(self.date_entry_opened),
            "day": self.day,
            "device_name": self.data["device_name"],
            "disk": self.disk,
            "duration": abs(self.data["duration"]),
            "duration_time_base": self.data["duration_time_base"] or 1,
            "errors": self.errors,
            "extension": self.extension,
            "file_size": self.data["file_size"],
            "file_title": self.file_title,
            "file_title_numeric": self.file_title_numeric,
            "filename": str(self.filename),
            "filename_numeric": self.filename_numeric,
            "found": self.data["is_file"],
            "frame_rate": self.frame_rate,
            "frame_rate_den": self.data["frame_rate_den"] or 1,
            "frame_rate_num": self.data["frame_rate_num"],
            "height": self.data["height"],
            "length": str(self.length),
            "meta_title": self.data["meta_title"],
            "meta_title_numeric": self.meta_title_numeric,
            "move_id": self.move_id if with_moves else None,
            "moves": self.moves if with_moves else None,
            "not_found": not self.data["is_file"],
            "properties": self.json_properties,
            "readable": not self.data["unreadable"],
            "sample_rate": self.data["sample_rate"],
            "similarity_id": self.data["similarity_id"],
            "size": str(self.size),
            "size_length": str(self.size_length),
            "subtitle_languages": self.subtitle_languages,
            "thumbnail_path": self.thumbnail_base64,
            "title": self.title,
            "title_numeric": self.title_numeric,
            "video_codec": self.data["video_codec"],
            "video_codec_description": self.data["video_codec_description"],
            "video_id": self.data["video_id"],
            "width": self.data["width"],
            "with_thumbnails": self.data["with_thumbnails"],
        }
