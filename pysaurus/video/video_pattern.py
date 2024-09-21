import base64
from abc import ABC, abstractmethod
from typing import Dict, List, TypedDict

from pysaurus.core.components import AbsolutePath, Date, Duration, FileSize
from pysaurus.properties.properties import PropUnitType


class MoveType(TypedDict):
    video_id: int
    filename: str


class VideoPattern(ABC):
    __slots__ = ()

    def __eq__(self, other):
        return self.filename == other.filename

    @property
    @abstractmethod
    def filename(self) -> AbsolutePath:
        raise NotImplementedError()

    @property
    @abstractmethod
    def file_size(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def errors(self) -> List[str]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def video_id(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def mtime(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def date_entry_modified(self) -> Date:
        raise NotImplementedError()

    @property
    @abstractmethod
    def date_entry_opened(self) -> Date:
        raise NotImplementedError()

    @property
    @abstractmethod
    def audio_bit_rate(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def audio_bits(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def audio_codec(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def audio_codec_description(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def bit_depth(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def channels(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def container_format(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def device_name(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def driver_id(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def duration(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def duration_time_base(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def frame_rate_den(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def frame_rate_num(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def height(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def meta_title(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def similarity_id(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def video_codec(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def video_codec_description(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def width(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def discarded(self) -> bool:
        raise NotImplementedError()

    @property
    @abstractmethod
    def unreadable(self) -> bool:
        raise NotImplementedError()

    @property
    @abstractmethod
    def found(self) -> bool:
        raise NotImplementedError()

    @property
    @abstractmethod
    def with_thumbnails(self) -> bool:
        raise NotImplementedError()

    @property
    @abstractmethod
    def audio_languages(self) -> List[str]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def subtitle_languages(self) -> List[str]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def properties(self) -> Dict[str, List[PropUnitType]]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def moves(self) -> List[MoveType]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def thumbnail(self) -> bytes:
        raise NotImplementedError()

    @property
    def thumbnail_base64(self):
        # Return thumbnail as HTML, base64 encoded image data
        data: bytes = self.thumbnail
        return base64.b64encode(data).decode() if data else None

    @property
    def thumbnail_path(self):
        thumbnail = self.thumbnail_base64
        return f"data:image/jpeg;base64,{thumbnail}" if thumbnail else None

    @property
    def readable(self) -> bool:
        return not self.unreadable

    @property
    def not_found(self) -> bool:
        return not self.found

    @property
    def without_thumbnails(self) -> bool:
        return not self.with_thumbnails

    @property
    def date(self) -> Date:
        return Date(self.mtime)

    @property
    def bit_rate(self) -> FileSize:
        return FileSize(
            self.file_size * self.duration_time_base / self.duration
            if self.duration
            else 0
        )

    @property
    def length(self) -> Duration:
        return Duration(self.duration * 1000000 / self.duration_time_base)

    @property
    def raw_microseconds(self):
        return self.duration * 1000000 / self.duration_time_base

    @property
    def size(self) -> FileSize:
        return FileSize(self.file_size)

    def json(self, with_moves=False) -> dict:
        filename = self.filename
        standard_path = filename.standard_path
        file_title = filename.file_title
        title = self.meta_title or file_title
        return {
            "audio_bit_rate": self.audio_bit_rate,
            "audio_bits": self.audio_bits,
            "audio_codec": str(self.audio_codec),
            "audio_codec_description": str(self.audio_codec_description),
            "audio_languages": self.audio_languages,
            "bit_depth": self.bit_depth,
            "bit_rate": str(self.bit_rate),
            "channels": self.channels,
            "container_format": str(self.container_format),
            "date": str(self.date),
            "date_entry_modified": str(self.date_entry_modified),
            "date_entry_opened": str(self.date_entry_opened),
            # "day": self.day,
            # "year": self.year,
            # "device_name": self.data[F.device_name],
            # "disk": self.disk,
            # "duration": abs(self.data[F.duration]),
            # "duration_time_base": self.data[F.duration_time_base] or 1,
            "errors": list(self.errors),
            "extension": filename.extension,
            "file_size": self.file_size,
            "file_title": file_title,
            # "file_title_numeric": file_title,
            "filename": standard_path,
            # "filename_numeric": standard_path,
            "found": self.found,
            "frame_rate": (self.frame_rate_num / (self.frame_rate_den or 1)),
            # "frame_rate": self.frame_rate,
            # "frame_rate_den": self.data[F.frame_rate_den] or 1,
            # "frame_rate_num": self.data[F.frame_rate_num],
            "height": self.height,
            "length": str(self.length),
            # "meta_title": self.data[F.meta_title],
            # "meta_title_numeric": self.data[F.meta_title],
            # "move_id": self.move_id if with_moves else None,
            "moves": self.moves if with_moves else None,
            # "not_found": not self.data[F.is_file],
            "properties": self.properties,
            "readable": not self.unreadable,
            "sample_rate": self.sample_rate,
            "similarity_id": self.similarity_id,
            "size": str(self.size),
            # "size_length": str(self.size_length),
            "subtitle_languages": self.subtitle_languages,
            "thumbnail_path": self.thumbnail_path,
            "thumbnail_base64": self.thumbnail_base64,
            "title": title,
            # "title_numeric": title,
            "video_codec": str(self.video_codec),
            "video_codec_description": str(self.video_codec_description),
            "video_id": self.video_id,
            "width": self.width,
            "with_thumbnails": self.with_thumbnails,
        }
