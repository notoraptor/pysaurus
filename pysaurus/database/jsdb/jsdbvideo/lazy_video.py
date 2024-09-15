import os
from copy import deepcopy
from typing import Any, Dict, List

from pysaurus.core.classes import StringPrinter, StringedTuple, Text
from pysaurus.core.compare import to_comparable
from pysaurus.core.components import AbsolutePath, Date, Duration, FileSize
from pysaurus.core.constants import UNDEFINED
from pysaurus.core.functions import class_get_public_attributes, string_to_pieces
from pysaurus.core.modules import FNV64
from pysaurus.core.schematizable import WithSchema
from pysaurus.core.semantic_text import SemanticText
from pysaurus.video.video_schema import VIDEO_SCHEMA
from pysaurus.video.video_sorting import VideoSorting


class LazyVideo(WithSchema):
    __slots__ = ("__discarded", "database")
    SCHEMA = VIDEO_SCHEMA
    __protected__ = (
        "database",
        "runtime",
        "discarded",
        "thumbnail_base64",
        "thumbnail_blob",
    )

    def __init__(self, database, short_dict: dict, discarded=False):
        from pysaurus.database.jsdb.json_database import JsonDatabase

        super().__init__(short_dict)
        # Runtime
        self.__discarded = discarded
        self.database: JsonDatabase = database

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

    def _set(self, name, value) -> bool:
        modified = super()._set(name, value)
        if modified and self.database:
            self.database.jsondb_register_modified(self)
        return modified

    @property
    def discarded(self):
        return self.__discarded

    @discarded.setter
    def discarded(self, discarded: bool):
        if self.__discarded != discarded:
            self.__discarded = discarded
            self.database.jsondb_register_modified(self)

    @property
    def filename(self):
        return AbsolutePath(self._get("filename"))

    def with_new_filename(self, filename):
        assert isinstance(filename, (str, AbsolutePath))
        d = deepcopy(self._d)
        assert self.SCHEMA.set_into_short_dict(d, "filename", str(filename))
        video = LazyVideo(self.database, d, discarded=self.__discarded)

        stats = os.stat(video.filename.path)
        runtime = video.runtime
        runtime.driver_id = stats.st_dev
        video.runtime = runtime
        video._save_date_entry_modified()
        return video

    file_size = property(lambda self: self._get("file_size"))
    errors = property(lambda self: set(self._get("errors")))

    @property
    def video_id(self):
        return self._get("video_id")

    @video_id.setter
    def video_id(self, data):
        self._set("video_id", data)

    @property
    def runtime(self):
        return self._get("runtime")

    @runtime.setter
    def runtime(self, data):
        self._set("runtime", data.to_dict())

    @property
    def thumb_name(self):
        # Set if necessary, then get
        if not self._get("thumb_name"):
            self._set("thumb_name", FNV64.hash(self.filename.standard_path))
        return self._get("thumb_name")

    @thumb_name.setter
    def thumb_name(self, data):
        self._set("thumb_name", data)

    @property
    def date_entry_modified(self):
        if self._get("date_entry_modified") is None:
            self._set("date_entry_modified", self.runtime.mtime)
        return Date(self._get("date_entry_modified"))

    @date_entry_modified.setter
    def date_entry_modified(self, data):
        self._set("date_entry_modified", data)

    @property
    def date_entry_opened(self):
        if self._get("date_entry_opened") is None:
            self._set("date_entry_opened", self.runtime.mtime)
        return Date(self._get("date_entry_opened"))

    @property
    def already_opened(self) -> bool:
        return self.date != self.date_entry_opened

    @date_entry_opened.setter
    def date_entry_opened(self, data):
        self._set("date_entry_opened", data)

    unreadable = property(lambda self: self._get("unreadable"))
    audio_bit_rate = property(lambda self: self._get("audio_bit_rate"))
    audio_codec = property(lambda self: Text(self._get("audio_codec")))
    audio_codec_description = property(
        lambda self: Text(self._get("audio_codec_description"))
    )
    bit_depth = property(lambda self: self._get("bit_depth"))
    channels = property(lambda self: self._get("channels"))
    container_format = property(lambda self: Text(self._get("container_format")))
    device_name = property(lambda self: Text(self._get("device_name")))
    duration = property(lambda self: abs(self._get("duration")))
    duration_time_base = property(lambda self: self._get("duration_time_base") or 1)
    frame_rate_den = property(lambda self: self._get("frame_rate_den") or 1)
    frame_rate_num = property(lambda self: self._get("frame_rate_num"))
    height = property(lambda self: self._get("height"))

    @property
    def meta_title(self) -> Text:
        return Text(self._get("meta_title"))

    @property
    def properties(self) -> Dict[str, List[Any]]:
        return self._get("properties")

    @properties.setter
    def properties(self, properties: Dict[str, List[Any]]):
        self._set("properties", properties)

    sample_rate = property(lambda self: self._get("sample_rate"))

    @property
    def similarity_id(self):
        return self._get("similarity_id")

    @similarity_id.setter
    def similarity_id(self, data):
        if self._set("similarity_id", data):
            self._save_date_entry_modified()

    video_codec = property(lambda self: Text(self._get("video_codec")))
    video_codec_description = property(
        lambda self: Text(self._get("video_codec_description"))
    )
    width = property(lambda self: self._get("width"))
    audio_languages = property(lambda self: self._get("audio_languages"))
    subtitle_languages = property(lambda self: self._get("subtitle_languages"))
    audio_bits = property(lambda self: self._get("audio_bits"))

    # Derived attributes

    extension = property(lambda self: self.filename.extension)
    file_title = property(lambda self: Text(self.filename.file_title))
    file_title_numeric = property(lambda self: SemanticText(self.filename.file_title))
    size = property(lambda self: FileSize(self.file_size))
    day = property(lambda self: self.date.day)
    year = property(lambda self: self.date.year)
    # runtime attributes
    disk = property(
        lambda self: self.filename.get_drive_name() or self.runtime.driver_id
    )
    date = property(lambda self: Date(self.runtime.mtime))

    readable = property(lambda self: not self.unreadable)

    mtime = property(lambda self: self.runtime.mtime)
    driver_id = property(lambda self: self.runtime.driver_id)

    @property
    def found(self) -> bool:
        return self.runtime.is_file

    @found.setter
    def found(self, is_file: bool):
        if self.runtime.is_file != is_file:
            self.runtime.is_file = is_file
            self.database.jsondb_register_modified(self)

    not_found = property(lambda self: not self.found)
    with_thumbnails = property(
        lambda self: self.database.jsondb_has_thumbnail(self.filename)
    )
    without_thumbnails = property(lambda self: not self.with_thumbnails)

    frame_rate = property(lambda self: self.frame_rate_num / self.frame_rate_den)
    length = property(
        lambda self: Duration(round(self.duration * 1000000 / self.duration_time_base))
    )
    title = property(
        lambda self: (
            self.meta_title if self.meta_title else Text(self.filename.file_title)
        )
    )
    title_numeric = property(
        lambda self: (
            self.meta_title_numeric if self.meta_title else self.file_title_numeric
        )
    )
    filename_numeric = property(lambda self: SemanticText(self.filename.standard_path))
    meta_title_numeric = property(lambda self: SemanticText(self.meta_title.value))
    raw_seconds = property(lambda self: self.duration / self.duration_time_base)
    raw_microseconds = property(
        lambda self: self.duration * 1000000 / self.duration_time_base
    )
    thumbnail_base64 = property(
        lambda self: self.database.jsondb_get_thumbnail_base64(self.filename)
    )
    thumbnail_blob = property(
        lambda self: self.database.jsondb_get_thumbnail_blob(self.filename)
    )
    size_length = property(lambda self: StringedTuple((self.size, self.length)))
    filename_length = property(lambda self: len(self.filename))

    @property
    def thumbnail_path(self):
        thumbnail = self.thumbnail_base64
        return f"data:image/jpeg;base64,{thumbnail}" if thumbnail else None

    @property
    def expected_raw_size(self):
        return FileSize(
            (
                self.frame_rate
                * self.width
                * self.height
                * 3
                * (self.bit_depth or 8)
                / 8
                + self.sample_rate * (self.audio_bits or 32) / 8
            )
            * self.raw_seconds
        )

    @property
    def bit_rate(self):
        return FileSize(
            self.file_size * self.duration_time_base / self.duration
            if self.duration
            else 0
        )

    @property
    def move_id(self):
        return self.database.moves_attribute(self.video_id)[0]

    @property
    def moves(self):
        return self.database.moves_attribute(self.video_id)[1]

    # Methods.

    def add_errors(self, errors):
        self._set("errors", sorted(self.errors | set(errors)))

    def terms(self) -> List[str]:
        term_sources = [self.filename.path, str(self.meta_title)]
        for name, val in self.properties.items():
            if self.database.get_prop_types(name=name, with_type=str):
                term_sources.extend(val)
        all_str = " ".join(term_sources)
        t_all_str = string_to_pieces(all_str)
        t_all_str_low = string_to_pieces(all_str.lower())
        return t_all_str if t_all_str == t_all_str_low else (t_all_str + t_all_str_low)

    def has_exact_text(self, text: str) -> bool:
        text = text.lower()
        return (
            text in self.filename.path.lower()
            or text in self.meta_title.value.lower()
            or any(
                text in [v.lower() for v in val]
                for name, val in self._get("properties").items()
                if self.database.get_prop_types(name=name, with_type=str)
            )
        )

    def to_comparable(self, sorting: VideoSorting) -> list:
        return [
            to_comparable(getattr(self, field), reverse) for field, reverse in sorting
        ]

    def has_property(self, name):
        return name in self._get("properties")

    def get_property(self, name, default_unit=UNDEFINED) -> List[Any]:
        props = self.properties
        return props.get(name, [] if default_unit is UNDEFINED else [default_unit])

    def remove_property(self, name) -> list:
        self._save_date_entry_modified()
        properties = self._get("properties")
        popped = properties.pop(name, [])
        if popped:
            self._set("properties", properties)
        return popped

    def set_property(self, name, value) -> bool:
        assert value is not None
        value = sorted(value) if isinstance(value, list) else [value]
        modified = False
        properties = self.properties
        if self.database.jsondb_prop_val_is_default(name, value):
            if name in properties:
                modified = True
                del properties[name]
        elif name not in properties or properties[name] != value:
            modified = True
            properties[name] = value
        if modified:
            self._set("properties", properties)
            self._save_date_entry_modified()
        return modified

    def _save_date_entry_modified(self):
        self._set("date_entry_modified", Date.now().time)
