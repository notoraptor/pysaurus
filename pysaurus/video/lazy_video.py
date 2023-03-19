from typing import Any, Dict, Set

from pysaurus.core.classes import StringPrinter, StringedTuple, Text
from pysaurus.core.compare import to_comparable
from pysaurus.core.components import AbsolutePath, Date, Duration, FileSize
from pysaurus.core.constants import JPEG_EXTENSION, PYTHON_ERROR_THUMBNAIL
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
    __slots__ = ("discarded", "database")
    SCHEMA = VideoSchema()
    __protected__ = ("database", "runtime", "discarded")
    FLAGS = {
        "readable",
        "unreadable",
        "found",
        "not_found",
        "with_thumbnails",
        "without_thumbnails",
    }

    def __init__(self, database, short_dict: dict):
        super().__init__(short_dict)
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

    @property
    def filename(self):
        return AbsolutePath(self._get("filename"))

    @filename.setter
    def filename(self, data):
        assert isinstance(data, (str, AbsolutePath))
        self._set("filename", str(data))
        self._save_date_entry_modified()

    file_size = property(lambda self: self._get("file_size"))
    errors = property(lambda self: set(self._get("errors")))

    @property
    def video_id(self):
        return self._get("video_id")

    @video_id.setter
    def video_id(self, data):
        self._set("video_id", data)

    runtime = property(lambda self: self._get("runtime"))

    @property
    def thumb_name(self):
        # Set if necessary, then get
        if not self._get("thumb_name"):
            self._set("thumb_name", FNV64.hash(self.filename.standard_path))
        return self._get("thumb_name")

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
    meta_title = property(lambda self: Text(self._get("meta_title")))

    @property
    def properties(self):
        return {
            name: self.database.get_prop_val(name, value)
            for name, value in self._get("properties").items()
        }

    sample_rate = property(lambda self: self._get("sample_rate"))

    @property
    def similarity_id(self):
        return self._get("similarity_id")

    @similarity_id.setter
    def similarity_id(self, data):
        if self._get("similarity_id") != data:
            self._set("similarity_id", data)
            self._save_date_entry_modified()

    video_codec = property(lambda self: Text(self._get("video_codec")))
    video_codec_description = property(
        lambda self: Text(self._get("video_codec_description"))
    )
    width = property(lambda self: self._get("width"))
    audio_languages = property(lambda self: self._get("audio_languages"))
    subtitle_languages = property(lambda self: self._get("subtitle_languages"))

    # Derived properties

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
        return [
            {"video_id": video.video_id, "filename": video.filename}
            for video in self.database.moves_attribute(self)[1]
        ]

    def terms(self, as_set=False):
        term_sources = [self.filename.path, str(self.meta_title)]
        for name, val in self.properties.items():
            if self.database.has_prop_type(name, with_type=str):
                if isinstance(val, list):
                    term_sources.extend(val)
                else:
                    term_sources.append(val)
        all_str = " ".join(term_sources)
        t_all_str = string_to_pieces(all_str, as_set=False)
        t_all_str_low = string_to_pieces(all_str.lower(), as_set=False)
        t_all = t_all_str if t_all_str == t_all_str_low else (t_all_str + t_all_str_low)
        return set(t_all) if as_set else t_all

    def to_comparable(self, sorting: VideoSorting) -> list:
        return [
            to_comparable(getattr(self, field), reverse) for field, reverse in sorting
        ]

    def has_property(self, name):
        return name in self._get("properties")

    def get_property(self, name, *default):
        properties = self.properties
        return properties.get(name, *default) if default else properties[name]

    def remove_property(self, name, *default):
        self._save_date_entry_modified()
        properties = self._get("properties")
        popped = properties.pop(name, *default)
        self._set("properties", properties)
        return popped

    def set_validated_properties(self, properties: Dict[str, Any]) -> Set[str]:
        return self.set_properties(
            {
                name: self.database.get_prop_val(name, value)
                for name, value in properties.items()
            }
        )

    def set_properties(self, properties: Dict[str, Any]) -> Set[str]:
        return {
            name for name, value in properties.items() if self.set_property(name, value)
        }

    def set_property(self, name, value) -> bool:
        modified = False
        properties = self.properties
        if value is None:
            if name in properties:
                modified = True
                del properties[name]
        else:
            if name not in properties or properties[name] != value:
                modified = True
            properties[name] = value
        self._set("properties", properties)
        self._save_date_entry_modified(modified)
        return modified

    def open(self):
        self.filename.open()
        self._set("date_entry_opened", Date.now().time)

    def _save_date_entry_modified(self, save=True):
        if save:
            self._set("date_entry_modified", Date.now().time)
