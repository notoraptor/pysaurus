from abc import ABCMeta, abstractmethod

from pysaurus.core.classes import StringedTuple, Text
from pysaurus.core.components import AbsolutePath, Date, Duration, FileSize
from pysaurus.core.semantic_text import SemanticText


class AbstractVideoParser(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def filename(self, value):
        pass

    @abstractmethod
    def video_id(self, value):
        pass

    @abstractmethod
    def file_size(self, value):
        pass

    @abstractmethod
    def unreadable(self, value):
        pass

    @abstractmethod
    def audio_bit_rate(self, value):
        pass

    @abstractmethod
    def audio_bits(self, value):
        pass

    @abstractmethod
    def audio_codec(self, value):
        pass

    @abstractmethod
    def audio_codec_description(self, value):
        pass

    @abstractmethod
    def bit_depth(self, value):
        pass

    @abstractmethod
    def channels(self, value):
        pass

    @abstractmethod
    def container_format(self, value):
        pass

    @abstractmethod
    def device_name(self, value):
        pass

    @abstractmethod
    def duration(self, value):
        pass

    @abstractmethod
    def duration_time_base(self, value):
        pass

    @abstractmethod
    def frame_rate_den(self, value):
        pass

    @abstractmethod
    def frame_rate_num(self, value):
        pass

    @abstractmethod
    def height(self, value):
        pass

    @abstractmethod
    def meta_title(self, value):
        pass

    @abstractmethod
    def sample_rate(self, value):
        pass

    @abstractmethod
    def video_codec(self, value):
        pass

    @abstractmethod
    def video_codec_description(self, value):
        pass

    @abstractmethod
    def width(self, value):
        pass

    @abstractmethod
    def mtime(self, value):
        pass

    @abstractmethod
    def driver_id(self, value):
        pass

    @abstractmethod
    def is_file(self, value):
        pass

    @abstractmethod
    def discarded(self, value):
        pass

    @abstractmethod
    def date_entry_modified(self, value):
        pass

    @abstractmethod
    def date_entry_opened(self, value):
        pass

    @abstractmethod
    def similarity_id(self, value):
        pass

    @abstractmethod
    def found(self, value):
        pass

    @abstractmethod
    def with_thumbnails(self, value):
        pass


class QueryVideoParser(AbstractVideoParser):
    pass


class BasicVideoGetter(AbstractVideoParser):
    __slots__ = ()

    def filename(self, value) -> AbsolutePath:
        return AbsolutePath.ensure(value)

    def video_id(self, value):
        return value

    def file_size(self, value) -> int:
        return value

    def unreadable(self, value):
        return value

    def audio_bit_rate(self, value):
        return value

    def audio_bits(self, value):
        return value

    def audio_codec(self, value):
        return value

    def audio_codec_description(self, value):
        return value

    def bit_depth(self, value):
        return value

    def channels(self, value):
        return value

    def container_format(self, value):
        return value

    def device_name(self, value):
        return value

    def duration(self, value):
        return value

    def duration_time_base(self, value):
        return value

    def frame_rate_den(self, value):
        return value

    def frame_rate_num(self, value):
        return value

    def height(self, value):
        return value

    def meta_title(self, value):
        return value

    def sample_rate(self, value):
        return value

    def video_codec(self, value):
        return value

    def video_codec_description(self, value):
        return value

    def width(self, value):
        return value

    def mtime(self, value):
        return value

    def driver_id(self, value):
        return value

    def is_file(self, value):
        return value

    def discarded(self, value):
        return value

    def date_entry_modified(self, value):
        return value

    def date_entry_opened(self, value):
        return value

    def similarity_id(self, value):
        return value

    def found(self, value):
        return value

    def with_thumbnails(self, value):
        return value


class CompleteVideoGetter:
    def __init__(self, data: dict):
        self.data = data
        self.getter = BasicVideoGetter()

    @property
    def filename(self):
        return self.getter.filename(self.data["filename"])

    @property
    def video_id(self):
        return self.getter.video_id(self.data["video_id"])

    @property
    def file_size(self):
        return self.getter.file_size(self.data["file_size"])

    @property
    def unreadable(self):
        return self.getter.unreadable(self.data["unreadable"])

    @property
    def audio_bit_rate(self):
        return self.getter.audio_bit_rate(self.data["audio_bit_rate"])

    @property
    def audio_bits(self):
        return self.getter.audio_bits(self.data["audio_bits"])

    @property
    def audio_codec(self):
        return self.getter.audio_codec(self.data["audio_codec"])

    @property
    def audio_codec_description(self):
        return self.getter.audio_codec_description(self.data["audio_codec_description"])

    @property
    def bit_depth(self):
        return self.getter.bit_depth(self.data["bit_depth"])

    @property
    def channels(self):
        return self.getter.channels(self.data["channels"])

    @property
    def container_format(self):
        return self.getter.container_format(self.data["container_format"])

    @property
    def device_name(self):
        return self.getter.device_name(self.data["device_name"])

    @property
    def duration(self):
        return self.getter.duration(self.data["duration"])

    @property
    def duration_time_base(self):
        return self.getter.duration_time_base(self.data["duration_time_base"])

    @property
    def frame_rate_den(self):
        return self.getter.frame_rate_den(self.data["frame_rate_den"])

    @property
    def frame_rate_num(self):
        return self.getter.frame_rate_num(self.data["frame_rate_num"])

    @property
    def height(self):
        return self.getter.height(self.data["height"])

    @property
    def meta_title(self):
        return self.getter.meta_title(self.data["meta_title"])

    @property
    def sample_rate(self):
        return self.getter.sample_rate(self.data["sample_rate"])

    @property
    def video_codec(self):
        return self.getter.video_codec(self.data["video_codec"])

    @property
    def video_codec_description(self):
        return self.getter.video_codec_description(self.data["video_codec_description"])

    @property
    def width(self):
        return self.getter.width(self.data["width"])

    @property
    def mtime(self):
        return self.getter.mtime(self.data["mtime"])

    @property
    def driver_id(self):
        return self.getter.driver_id(self.data["driver_id"])

    @property
    def is_file(self):
        return self.getter.is_file(self.data["is_file"])

    @property
    def discarded(self):
        return self.getter.discarded(self.data["discarded"])

    @property
    def date_entry_modified(self):
        return self.getter.date_entry_modified(self.data["date_entry_modified"])

    @property
    def date_entry_opened(self):
        return self.getter.date_entry_opened(self.data["date_entry_opened"])

    @property
    def similarity_id(self):
        return self.getter.similarity_id(self.data["similarity_id"])

    # derived

    @property
    def found(self):
        return self.getter.found(self.data["found"])

    @property
    def with_thumbnails(self):
        return self.getter.with_thumbnails(self.data["with_thumbnails"])

    @property
    def extension(self):
        return self.filename.extension

    @property
    def file_title(self):
        return Text(self.filename.file_title)

    @property
    def file_title_numeric(self):
        return SemanticText(self.filename.file_title)

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
    def date(self):
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
        return self.meta_title or Text(self.filename.file_title)

    @property
    def title_numeric(self):
        return self.meta_title_numeric if self.meta_title else self.file_title_numeric

    @property
    def filename_numeric(self):
        return SemanticText(self.filename.standard_path)

    @property
    def meta_title_numeric(self):
        return SemanticText(self.meta_title.value)

    @property
    def raw_microseconds(self):
        return self.duration * 1000000 / self.duration_time_base

    @property
    def thumbnail_base64(self):
        data: bytes = self.data.get("thumbnail")
        return ("data:image/jpeg;base64," + data.decode()) if data else None

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

    @property
    def moves(self):
        return self.data.get("moves")
