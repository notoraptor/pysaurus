import os
from copy import deepcopy
from typing import Any

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.classes import StringPrinter, Text
from pysaurus.core.compare import to_comparable
from pysaurus.core.datestring import Date
from pysaurus.core.functions import class_get_public_attributes, string_to_pieces
from pysaurus.core.schematizable import Short, WithSchema
from pysaurus.core.semantic_text import SemanticText
from pysaurus.video.lazy_video_runtime_info import LazyVideoRuntimeInfo
from pysaurus.video.video_pattern import VideoPattern
from pysaurus.video.video_sorting import VideoSorting


class LazyVideo(WithSchema, VideoPattern):
    __slots__ = ("__discarded", "database")
    __schema_readonly__ = True

    # Fields with custom properties (default in annotation)
    filename: Short["f", str, None]
    errors: Short["e", list, []]
    video_id: Short["j", int, None]
    runtime: Short["R", LazyVideoRuntimeInfo, {}]
    date_entry_modified: Short["m", float, None]
    date_entry_opened: Short["o", float, None]
    audio_codec: Short["a", str, ""]
    audio_codec_description: Short["A", str, ""]
    container_format: Short["c", str, ""]
    device_name: Short["b", str, ""]
    duration: Short["d", float, 0.0]
    duration_time_base: Short["t", int, 0]
    frame_rate_den: Short["y", int, 0]
    meta_title: Short["n", str, ""]
    properties: Short["p", dict, {}]
    similarity_id: Short["S", int, None]
    similarity_id_reencoded: Short["E", int, None]
    watched: Short["O", bool, False]
    video_codec: Short["v", str, ""]
    video_codec_description: Short["V", str, ""]

    # Fields with auto-generated readonly properties
    file_size: Short["s", int] = 0
    unreadable: Short["U", bool] = False
    audio_bit_rate: Short["r", int] = 0
    audio_bits: Short["B", int] = 0
    audio_languages: Short["l", list] = []
    bit_depth: Short["D", int] = 0
    channels: Short["C", int] = 0
    frame_rate_num: Short["x", int] = 0
    height: Short["h", int] = 0
    sample_rate: Short["u", int] = 0
    subtitle_languages: Short["L", list] = []
    width: Short["w", int] = 0

    __protected__ = (
        "database",
        "runtime",
        "discarded",
        "thumbnail_base64",
        "thumbnail",
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

    errors = property(lambda self: sorted(set(self._get("errors"))))

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

    audio_codec = property(lambda self: Text(self._get("audio_codec")))
    audio_codec_description = property(
        lambda self: Text(self._get("audio_codec_description"))
    )
    container_format = property(lambda self: Text(self._get("container_format")))
    device_name = property(lambda self: Text(self._get("device_name")))
    duration = property(lambda self: abs(self._get("duration")))
    duration_time_base = property(lambda self: self._get("duration_time_base") or 1)
    frame_rate_den = property(lambda self: self._get("frame_rate_den") or 1)

    @property
    def meta_title(self) -> Text:
        return Text(self._get("meta_title"))

    @property
    def properties(self) -> dict[str, list[Any]]:
        return self._get("properties")

    @properties.setter
    def properties(self, properties: dict[str, list[Any]]):
        self._set("properties", properties)

    @property
    def similarity_id(self):
        return self._get("similarity_id")

    @similarity_id.setter
    def similarity_id(self, data):
        if self._set("similarity_id", data):
            self._save_date_entry_modified()

    @property
    def similarity_id_reencoded(self):
        return self._get("similarity_id_reencoded")

    @similarity_id_reencoded.setter
    def similarity_id_reencoded(self, data):
        if self._set("similarity_id_reencoded", data):
            self._save_date_entry_modified()

    @property
    def watched(self) -> bool:
        return self._get("watched")

    @watched.setter
    def watched(self, data):
        if self._set("watched", bool(data)):
            self._save_date_entry_modified()

    video_codec = property(lambda self: Text(self._get("video_codec")))
    video_codec_description = property(
        lambda self: Text(self._get("video_codec_description"))
    )

    # Derived attributes

    file_title = property(lambda self: Text(self.filename.file_title))
    # runtime attributes
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

    with_thumbnails = property(
        lambda self: self.database.jsondb_has_thumbnail(self.filename)
    )

    meta_title_numeric = property(lambda self: SemanticText(self.meta_title.value))
    thumbnail_base64 = property(
        lambda self: self.database.jsondb_get_thumbnail_base64(self.filename)
    )

    @property
    def thumbnail(self) -> bytes:
        return self.database.jsondb_get_thumbnail_blob(self.filename)

    @property
    def move_id(self):
        return self.database.moves_attribute(self.video_id)[0]

    @property
    def moves(self):
        return self.database.moves_attribute(self.video_id)[1]

    # Methods.

    def add_errors(self, errors):
        self._set("errors", sorted(self.errors | set(errors)))

    def terms(self) -> list[str]:
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
                text in v.lower()
                for name, val in self._get("properties").items()
                if self.database.get_prop_types(name=name, with_type=str)
                for v in val
            )
        )

    def to_comparable(self, sorting: VideoSorting) -> list:
        return [
            to_comparable(getattr(self, field), reverse) for field, reverse in sorting
        ]

    def has_property(self, name):
        return name in self._get("properties")

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
