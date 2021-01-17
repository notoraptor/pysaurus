"""
Video class. Properties:

- length: Return a Duration object representing the video duration.
  Based on raw duration fields `duration` and `duration_time_base`, we have: ::

    duration = (number of seconds) * duration_time_base

  So: ::

    (number of seconds) = duration / duration_time_base
"""

import base64
import sys
from io import BytesIO
from typing import Sequence

from pysaurus.core.classes import StringPrinter
from pysaurus.core.components import AbsolutePath, Duration
from pysaurus.core.constants import THUMBNAIL_EXTENSION
from pysaurus.core.database import path_utils
from pysaurus.core.database.video_state import VideoState
from pysaurus.core.functions import html_to_title, string_to_pieces
from pysaurus.core.modules import VideoClipping, ImageUtils


def compare_with_lt(v1, v2):
    return -1 if v1 < v2 else (1 if v2 < v1 else 0)


def compare_text(v1: str, v2: str):
    return compare_with_lt(v1.lower(), v2.lower()) or compare_with_lt(v1, v2)


def compare_text_or_data(v1, v2):
    return compare_text(v1, v2) if isinstance(v1, str) else compare_with_lt(v1, v2)


class Video(VideoState):
    UNREADABLE = False

    __slots__ = (
        # Video properties
        "audio_bit_rate",
        "audio_codec",
        "audio_codec_description",
        "channels",
        "container_format",
        "device_name",  # private field
        "duration",
        "duration_time_base",
        "frame_rate_den",
        "frame_rate_num",
        "height",
        "meta_title",
        "properties",
        "sample_rate",
        "thumb_name",
        "video_codec",
        "video_codec_description",
        "width",
        # Runtime attributes
        "runtime_has_thumbnail",
    )

    # TODO to remove
    STRING_FIELDS = {
        "audio_codec",
        "audio_codec_description",
        "container_format",
        "day",
        "disk",
        "extension",
        "file_size",
        "file_title",
        "filename",
        "thumbnail_path",
        "title",
        "video_codec",
        "video_codec_description",
        "meta_title",
    }

    # All video properties must be represented here.
    # Runtime attributes should not appear here.
    MIN_TO_LONG = {
        "A": "audio_codec_description",
        "C": "channels",
        "V": "video_codec_description",
        "a": "audio_codec",
        "b": "device_name",
        "c": "container_format",
        "d": "duration",
        "h": "height",
        "i": "thumb_name",
        "n": "meta_title",
        "p": "properties",
        "r": "audio_bit_rate",
        "t": "duration_time_base",
        "u": "sample_rate",
        "v": "video_codec",
        "w": "width",
        "x": "frame_rate_num",
        "y": "frame_rate_den",
    }

    LONG_TO_MIN = {_long: _min for _min, _long in MIN_TO_LONG.items()}

    QUALITY_FIELDS = (
        ("quality_compression", 6),
        ("height", 5),
        ("width", 4),
        ("raw_seconds", 3),
        ("frame_rate", 2),
        ("file_size", 1),
        ("audio_bit_rate", 0.5),
    )

    # TODO to remove
    ROW_FIELDS = (
        "audio_bit_rate",
        "audio_codec",
        "audio_codec_description",
        "container_format",
        "channels",
        "date",
        "day",
        "disk",
        "extension",
        "file_size",
        "file_title",
        "filename",
        "frame_rate",
        "height",
        "length",
        "properties",
        "quality",
        "sample_rate",
        "size",
        "thumbnail_path",
        "title",
        "video_codec",
        "video_codec_description",
        "video_id",
        "width",
    )

    def __init__(
        self,
        # Runtime arguments
        database,
        from_dictionary=None,
        # VideoState optional arguments
        filename=None,
        size=0,
        errors=(),
        video_id=None,
        # Video optional arguments
        audio_bit_rate=0,
        audio_codec="",
        audio_codec_description="",
        channels=2,
        container_format="",
        device_name="",
        duration=0,
        duration_time_base=0,
        frame_rate_den=0,
        frame_rate_num=0,
        height=0,
        meta_title="",
        properties=None,
        sample_rate=0,
        thumb_name="",
        video_codec="",
        video_codec_description="",
        width=0,
    ):
        """
        :type database: pysaurus.core.database.database.Database
        :type from_dictionary: dict
        :type filename: AbsolutePath | str
        :type size: int
        :type errors: set
        :type video_id: int, optional
        :type audio_bit_rate: int
        :type audio_codec: str
        :type audio_codec_description: str
        :type channels: int
        :type container_format: str
        :type device_name: str
        :type duration: int
        :type duration_time_base: int
        :type frame_rate_den: int
        :type frame_rate_num: int
        :type height: int
        :type meta_title: str
        :type properties: dict
        :type sample_rate: float
        :type thumb_name: str
        :type video_codec: str
        :type video_codec_description: str
        :type width: int
        """
        if from_dictionary:
            audio_bit_rate = from_dictionary.get(
                self.LONG_TO_MIN["audio_bit_rate"], audio_bit_rate
            )
            audio_codec = from_dictionary.get(
                self.LONG_TO_MIN["audio_codec"], audio_codec
            )
            audio_codec_description = from_dictionary.get(
                self.LONG_TO_MIN["audio_codec_description"], audio_codec_description
            )
            channels = from_dictionary.get(self.LONG_TO_MIN["channels"], channels)
            container_format = from_dictionary.get(
                self.LONG_TO_MIN["container_format"], container_format
            )
            device_name = from_dictionary.get(
                self.LONG_TO_MIN["device_name"], device_name
            )
            duration = from_dictionary.get(self.LONG_TO_MIN["duration"], duration)
            duration_time_base = from_dictionary.get(
                self.LONG_TO_MIN["duration_time_base"], duration_time_base
            )
            frame_rate_den = from_dictionary.get(
                self.LONG_TO_MIN["frame_rate_den"], frame_rate_den
            )
            frame_rate_num = from_dictionary.get(
                self.LONG_TO_MIN["frame_rate_num"], frame_rate_num
            )
            height = from_dictionary.get(self.LONG_TO_MIN["height"], height)
            meta_title = from_dictionary.get(self.LONG_TO_MIN["meta_title"], meta_title)
            properties = from_dictionary.get(self.LONG_TO_MIN["properties"], properties)
            sample_rate = from_dictionary.get(
                self.LONG_TO_MIN["sample_rate"], sample_rate
            )
            thumb_name = from_dictionary.get(self.LONG_TO_MIN["thumb_name"], thumb_name)
            video_codec = from_dictionary.get(
                self.LONG_TO_MIN["video_codec"], video_codec
            )
            video_codec_description = from_dictionary.get(
                self.LONG_TO_MIN["video_codec_description"], video_codec_description
            )
            width = from_dictionary.get(self.LONG_TO_MIN["width"], width)
        super(Video, self).__init__(
            filename=filename,
            size=size,
            errors=errors,
            video_id=video_id,
            database=database,
            from_dictionary=from_dictionary,
        )
        self.audio_bit_rate = audio_bit_rate
        self.audio_codec = audio_codec
        self.audio_codec_description = audio_codec_description
        self.container_format = container_format
        self.device_name = device_name
        self.duration = duration
        self.duration_time_base = duration_time_base or 1
        self.frame_rate_den = frame_rate_den or 1
        self.frame_rate_num = frame_rate_num
        self.height = height
        self.meta_title = html_to_title(meta_title)
        self.sample_rate = sample_rate
        self.thumb_name = thumb_name
        self.video_codec = video_codec
        self.video_codec_description = video_codec_description
        self.width = width
        self.channels = channels
        self.properties = {}

        self.set_properties(properties or {})
        self.runtime_has_thumbnail = False

    def __str__(self):
        with StringPrinter() as printer:
            printer.write("Video %s:" % self.video_id)
            for field in self.ROW_FIELDS:
                printer.write("\t%s: %s" % (field, getattr(self, field)))
            return str(printer)

    extension = property(lambda self: self.filename.extension)
    file_title = property(lambda self: self.filename.title)
    frame_rate = property(lambda self: self.frame_rate_num / self.frame_rate_den)
    length = property(
        lambda self: Duration(round(self.duration * 1000000 / self.duration_time_base))
    )
    title = property(
        lambda self: self.meta_title if self.meta_title else self.filename.title
    )

    raw_seconds = property(lambda self: self.duration / self.duration_time_base)
    raw_microseconds = property(
        lambda self: self.duration * 1000000 / self.duration_time_base
    )

    @property
    def thumbnail_path(self):
        return path_utils.generate_thumb_path(
            self.database.thumbnail_folder, self.ensure_thumbnail_name()
        )

    @property
    def quality(self):
        total_level = 0
        qualities = {}
        for field, level in self.QUALITY_FIELDS:
            value = getattr(self, field)
            min_value = self.database.video_interval.min[field]
            max_value = self.database.video_interval.max[field]
            if min_value == max_value:
                assert value == min_value, (value, min_value)
                quality = 0
            else:
                quality = (value - min_value) / (max_value - min_value)
                assert 0 <= quality <= 1, (quality, field, value, min_value, max_value)
            qualities[field] = quality * level
            total_level += level
        return sum(qualities.values()) * 100 / total_level

    @property
    def quality_compression(self):
        basic_file_size = (
            self.width * self.height * self.frame_rate * 3
            + self.sample_rate * self.channels * 2
        ) * self.raw_seconds
        return self.file_size / basic_file_size

    def ensure_thumbnail_name(self):
        if not self.thumb_name:
            self.thumb_name = path_utils.generate_thumb_name(self.filename)
            if self.database.system_is_case_insensitive:
                self.thumb_name = self.thumb_name.lower()
        return self.thumb_name

    def thumbnail_is_valid(self):
        return not self.error_thumbnail and self.runtime_has_thumbnail

    def thumbnail_to_base64(self):
        thumb_path = self.thumbnail_path
        if not thumb_path.isfile():
            return None
        image = ImageUtils.open_rgb_image(thumb_path.path)
        buffered = BytesIO()
        image.save(buffered, format=THUMBNAIL_EXTENSION)
        image_string = base64.b64encode(buffered.getvalue())
        return image_string

    def clip_to_base64(self, start, length):
        return VideoClipping.video_clip_to_base64(
            path=self.filename.path,
            time_start=start,
            clip_seconds=length,
            unique_id=self.ensure_thumbnail_name(),
        )

    def terms(self, as_set=False):
        return string_to_pieces(
            " ".join(
                (
                    self.filename.path,
                    self.meta_title,
                )
            ),
            as_set=as_set,
        )

    def has_terms_exact(self, terms):
        return " ".join(terms) in " ".join(self.terms())

    def has_terms_and(self, terms):
        video_terms = self.terms(as_set=True)
        return all(term in video_terms for term in terms)

    def has_terms_or(self, terms):
        video_terms = self.terms(as_set=True)
        return any(term in video_terms for term in terms)

    def to_dict(self):
        dct = super().to_dict()
        len_before = len(dct)
        for _min, _long in self.MIN_TO_LONG.items():
            assert _min not in dct, (_min, _long)
            dct[_min] = getattr(self, _long)
        assert len(dct) == len_before + len(self.MIN_TO_LONG)
        return dct

    @classmethod
    def from_dict(cls, dct, database):
        """
        :type dct: dict
        :type database: pysaurus.core.database.database.Database
        :rtype: Video
        """
        return cls(database=database, from_dictionary=dct)

    @staticmethod
    def compare(self, other, sorting):
        # type: (Video, Video, Sequence[str]) -> int
        for sort in sorting:
            reverse = sort[0] == "-"
            field = sort[1:]
            f1 = getattr(self, field)
            f2 = getattr(other, field)
            ret = compare_text_or_data(f1, f2)
            if ret:
                return -ret if reverse else ret
        return 0

    def set_properties(self, properties: dict):
        modified = set()
        for name, value in properties.items():
            if self.set_property(name, value):
                modified.add(name)
        return modified

    def set_property(self, name, value):
        if not self.database.has_prop_type(name):
            print("Unknown property: %s" % name, file=sys.stderr)
            return False
        prop_type = self.database.get_prop_type(name)
        value = prop_type(value)
        modified = name not in self.properties or self.properties[name] != value
        self.properties[name] = value
        return modified

    def remove_property(self, name):
        self.properties.pop(name, None)
