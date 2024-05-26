import base64
from typing import Iterable

from pysaurus.core.classes import StringedTuple
from pysaurus.core.components import AbsolutePath, Date, Duration, FileSize


class F:
    audio_bit_rate = 0
    audio_bits = 1
    audio_codec = 2
    audio_codec_description = 3
    bit_depth = 4
    channels = 5
    container_format = 6
    date_entry_modified = 7
    date_entry_opened = 8
    device_name = 9
    discarded = 10
    driver_id = 11
    duration = 12
    duration_time_base = 13
    file_size = 14
    filename = 15
    frame_rate_den = 16
    frame_rate_num = 17
    height = 18
    is_file = 19
    meta_title = 20
    mtime = 21
    sample_rate = 22
    similarity_id = 23
    unreadable = 24
    video_codec = 25
    video_codec_description = 26
    video_id = 27
    width = 28
    # Special fields, not from "video" table
    thumbnail = 29
    with_thumbnails = 30


def get_video_table_fields() -> Iterable[str]:
    return sorted(
        (
            field
            for field in dir(F)
            if "a" <= field[0] <= "z" and getattr(F, field) < F.thumbnail
        ),
        key=lambda field: getattr(F, field),
    )


VIDEO_TABLE_FIELD_NAMES = get_video_table_fields()

FORMATTED_VIDEO_TABLE_FIELDS = ", ".join(
    f"v.{field} AS {field}" for field in VIDEO_TABLE_FIELD_NAMES
)


class SQLVideoWrapper:
    __slots__ = (
        "data",
        "audio_languages",
        "subtitle_languages",
        "errors",
        "properties",
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
        self.properties = json_properties
        self.moves = moves  # list of dicts {video_id => int, filename => str}

    @property
    def filename(self) -> AbsolutePath:
        return AbsolutePath(self.data[F.filename])

    @property
    def video_id(self):
        return self.data[F.video_id]

    @property
    def file_size(self):
        return self.data[F.file_size]

    @property
    def unreadable(self):
        return self.data[F.unreadable]

    @property
    def audio_bit_rate(self):
        return self.data[F.audio_bit_rate]

    @property
    def audio_bits(self):
        return self.data[F.audio_bits]

    @property
    def audio_codec(self):
        return self.data[F.audio_codec]

    @property
    def audio_codec_description(self):
        return self.data[F.audio_codec_description]

    @property
    def bit_depth(self):
        return self.data[F.bit_depth]

    @property
    def channels(self):
        return self.data[F.channels]

    @property
    def container_format(self):
        return self.data[F.container_format]

    @property
    def device_name(self):
        return self.data[F.device_name]

    @property
    def duration(self):
        return abs(self.data[F.duration])

    @property
    def duration_time_base(self):
        return self.data[F.duration_time_base] or 1

    @property
    def frame_rate_den(self):
        return self.data[F.frame_rate_den] or 1

    @property
    def frame_rate_num(self):
        return self.data[F.frame_rate_num]

    @property
    def height(self):
        return self.data[F.height]

    @property
    def meta_title(self):
        return self.data[F.meta_title]

    @property
    def sample_rate(self):
        return self.data[F.sample_rate]

    @property
    def video_codec(self):
        return self.data[F.video_codec]

    @property
    def video_codec_description(self):
        return self.data[F.video_codec_description]

    @property
    def width(self):
        return self.data[F.width]

    @property
    def mtime(self):
        return self.data[F.mtime]

    @property
    def driver_id(self):
        return self.data[F.driver_id]

    @property
    def is_file(self):
        return self.data[F.is_file]

    @property
    def discarded(self):
        return self.data[F.discarded]

    @property
    def date_entry_modified(self) -> Date:
        value = self.data[F.date_entry_modified]
        return Date(value if value is not None else self.mtime)

    @property
    def date_entry_opened(self) -> Date:
        value = self.data[F.date_entry_opened]
        return Date(value if value is not None else self.mtime)

    @property
    def similarity_id(self):
        return self.data[F.similarity_id]

    # derived

    @property
    def found(self):
        return self.data[F.is_file]

    @property
    def with_thumbnails(self):
        return self.data[F.with_thumbnails]

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
    def year(self):
        return self.date.year

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
        return Duration(self.duration * 1000000 / self.duration_time_base)

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
        # Return thumbnail as HTML, base64 encoded image data
        data: bytes = self.data[F.thumbnail]
        return base64.b64encode(data).decode() if data else None

    @property
    def thumbnail_path(self):
        thumbnail = self.thumbnail_base64
        return f"data:image/jpeg;base64,{thumbnail}" if thumbnail else None

    @property
    def thumbnail_blob(self):
        return self.data["thumbnail"]

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
        filename = AbsolutePath(self.data[F.filename])
        standard_path = filename.standard_path
        file_title = filename.file_title
        title = self.data[F.meta_title] or file_title
        return {
            "audio_bit_rate": self.data[F.audio_bit_rate],
            "audio_bits": self.data[F.audio_bits],
            "audio_codec": self.data[F.audio_codec],
            "audio_codec_description": self.data[F.audio_codec_description],
            "audio_languages": self.audio_languages,
            "bit_depth": self.data[F.bit_depth],
            "bit_rate": str(self.bit_rate),
            "channels": self.data[F.channels],
            "container_format": self.data[F.container_format],
            "date": str(self.date),
            "date_entry_modified": str(self.date_entry_modified),
            "date_entry_opened": str(self.date_entry_opened),
            # "day": self.day,
            # "year": self.year,
            # "device_name": self.data[F.device_name],
            # "disk": self.disk,
            # "duration": abs(self.data[F.duration]),
            # "duration_time_base": self.data[F.duration_time_base] or 1,
            "errors": self.errors,
            "extension": filename.extension,
            "file_size": self.data[F.file_size],
            "file_title": file_title,
            # "file_title_numeric": file_title,
            "filename": standard_path,
            # "filename_numeric": standard_path,
            "found": self.data[F.is_file],
            "frame_rate": (
                self.data[F.frame_rate_num] / (self.data[F.frame_rate_den] or 1)
            ),
            # "frame_rate": self.frame_rate,
            # "frame_rate_den": self.data[F.frame_rate_den] or 1,
            # "frame_rate_num": self.data[F.frame_rate_num],
            "height": self.data[F.height],
            "length": str(self.length),
            # "meta_title": self.data[F.meta_title],
            # "meta_title_numeric": self.data[F.meta_title],
            # "move_id": self.move_id if with_moves else None,
            "moves": self.moves if with_moves else None,
            # "not_found": not self.data[F.is_file],
            "properties": self.properties,
            "readable": not self.data[F.unreadable],
            "sample_rate": self.data[F.sample_rate],
            "similarity_id": self.data[F.similarity_id],
            "size": str(self.size),
            # "size_length": str(self.size_length),
            "subtitle_languages": self.subtitle_languages,
            "thumbnail_path": self.thumbnail_path,
            "thumbnail_base64": self.thumbnail_base64,
            "title": title,
            # "title_numeric": title,
            "video_codec": self.data[F.video_codec],
            "video_codec_description": self.data[F.video_codec_description],
            "video_id": self.data[F.video_id],
            "width": self.data[F.width],
            "with_thumbnails": self.data[F.with_thumbnails],
        }
