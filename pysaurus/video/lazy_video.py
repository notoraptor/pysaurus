from copy import deepcopy
from typing import Any, Dict, List

from pysaurus.core.classes import StringPrinter, StringedTuple, Text
from pysaurus.core.compare import to_comparable
from pysaurus.core.components import AbsolutePath, Date, Duration, FileSize
from pysaurus.core.constants import JPEG_EXTENSION, PYTHON_ERROR_THUMBNAIL, UNDEFINED
from pysaurus.core.functions import (
    class_get_public_attributes,
    string_to_pieces,
)
from pysaurus.core.modules import FNV64
from pysaurus.core.schematizable import WithSchema
from pysaurus.core.semantic_text import SemanticText
from pysaurus.video.video_schema import VideoSchema
from pysaurus.video.video_sorting import VideoSorting


class LazyVideo(WithSchema):
    __slots__ = ("__discarded", "database")
    SCHEMA = VideoSchema()
    __protected__ = ("database", "runtime", "discarded")
    FLAGS = {
        "readable",
        "unreadable",
        "found",
        "not_found",
        "with_thumbnails",
        "without_thumbnails",
        "discarded",
    }

    def __init__(self, database, short_dict: dict, discarded=False):
        from pysaurus.database.json_database import JsonDatabase

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
        if modified:
            self.database.register_modified(self)
        return modified

    @property
    def discarded(self):
        return self.__discarded

    @discarded.setter
    def discarded(self, discarded: bool):
        if self.__discarded != discarded:
            self.__discarded = discarded
            self.database.register_modified(self)

    @property
    def filename(self):
        return AbsolutePath(self._get("filename"))

    def with_new_filename(self, filename):
        assert isinstance(filename, (str, AbsolutePath))
        d = deepcopy(self._d)
        assert self.SCHEMA.set_into_short_dict(d, "filename", str(filename))
        return LazyVideo(self.database, d, discarded=self.__discarded)

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

    @property
    def json_properties(self):
        return {
            name: (
                value if self.database.has_prop_type(name, multiple=True) else value[0]
            )
            for name, value in self._get("properties").items()
        }

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

    # Derived attributes

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

    @property
    def found(self) -> bool:
        return self.runtime.is_file

    @found.setter
    def found(self, is_file: bool):
        if self.runtime.is_file != is_file:
            self.runtime.is_file = is_file
            self.database.register_modified(self)

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
    quality = property(lambda self: self.database.quality_attribute(self))
    move_id = property(lambda self: self.database.moves_attribute(self)[0])
    size_length = property(lambda self: StringedTuple((self.size, self.length)))

    @property
    def unreadable_thumbnail(self):
        return PYTHON_ERROR_THUMBNAIL in self.errors

    @unreadable_thumbnail.setter
    def unreadable_thumbnail(self, has_error):
        errors = self.errors
        if has_error:
            errors.add(PYTHON_ERROR_THUMBNAIL)
        elif PYTHON_ERROR_THUMBNAIL in self.errors:
            errors.remove(PYTHON_ERROR_THUMBNAIL)
        self._set("errors", sorted(errors))

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
        return self.database.moves_attribute(self)[1]

    @property
    def has_runtime_thumbnail(self):
        return self.runtime.has_thumbnail

    @has_runtime_thumbnail.setter
    def has_runtime_thumbnail(self, value: bool):
        value = bool(value)
        if self.runtime.has_thumbnail != value:
            self.runtime.has_thumbnail = value
            self.database.register_modified(self)

    # Methods.

    def terms(self) -> List[str]:
        term_sources = [self.filename.path, str(self.meta_title)]
        for name, val in self.properties.items():
            if self.database.has_prop_type(name, with_type=str):
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
                if self.database.has_prop_type(name, with_type=str)
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

    def set_validated_properties(self, properties: Dict[str, Any]) -> List[str]:
        return self.set_properties(
            {
                name: self.database.new_prop_unit(name, value)
                for name, value in properties.items()
            }
        )

    def set_properties(self, properties: Dict[str, Any]) -> List[str]:
        return [
            name for name, value in properties.items() if self.set_property(name, value)
        ]

    def set_property(self, name, value) -> bool:
        assert value is not None
        value = sorted(value) if isinstance(value, list) else [value]
        modified = False
        properties = self.properties
        if self.database.value_is_default(name, value):
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

    def open(self):
        self.filename.open()
        self._set("date_entry_opened", Date.now().time)

    def _save_date_entry_modified(self):
        self._set("date_entry_modified", Date.now().time)
