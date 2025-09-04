from typing import Iterable

from pysaurus.core.classes import StringedTuple
from pysaurus.core.components import AbsolutePath
from pysaurus.core.datestring import Date
from pysaurus.properties.properties import PropUnitType
from pysaurus.video.video_pattern import MoveType, VideoPattern


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


class SQLVideoWrapper(VideoPattern):
    __slots__ = (
        "data",
        "_audio_languages",
        "_subtitle_languages",
        "_errors",
        "_properties",
        "_moves",
    )

    def __init__(
        self,
        data: dict,
        audio_languages=(),
        subtitle_languages=(),
        errors=(),
        json_properties: dict | None = None,
        moves=(),
    ):
        # Data must contains key "with_thumbnails"
        self.data = data
        self._audio_languages = audio_languages or []
        self._subtitle_languages = subtitle_languages or []
        self._errors = errors or []
        self._properties = json_properties or {}
        self._moves = moves or []  # list of dicts {video_id => int, filename => str}

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
    def errors(self) -> list[str]:
        return self._errors

    @property
    def audio_languages(self) -> list[str]:
        return self._audio_languages

    @property
    def subtitle_languages(self) -> list[str]:
        return self._subtitle_languages

    @property
    def properties(self) -> dict[str, list[PropUnitType]]:
        return self._properties

    @property
    def moves(self) -> list[MoveType]:
        return self._moves

    @property
    def thumbnail(self) -> bytes:
        return self.data[F.thumbnail]

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
    def day(self):
        return self.date.day

    @property
    def year(self):
        return self.date.year

    @property
    def disk(self):
        return self.filename.get_drive_name() or self.driver_id

    @property
    def frame_rate(self):
        return self.frame_rate_num / self.frame_rate_den

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
    def size_length(self):
        return StringedTuple((self.size, self.length))

    @property
    def filename_length(self):
        return len(self.filename)

    @property
    def move_id(self):
        return f"{self.size}, {self.length}"

    @errors.setter
    def errors(self, errors):
        self._errors = errors

    @audio_languages.setter
    def audio_languages(self, audio_languages):
        self._audio_languages = audio_languages

    @subtitle_languages.setter
    def subtitle_languages(self, subtitle_languages):
        self._subtitle_languages = subtitle_languages

    @properties.setter
    def properties(self, properties):
        self._properties = property

    @moves.setter
    def moves(self, moves):
        self._moves = moves
