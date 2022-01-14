"""
Video class. Properties:

- length: Return a Duration object representing the video duration.
  Based on raw duration fields `duration` and `duration_time_base`, we have: ::

    duration = (number of seconds) * duration_time_base

  So: ::

    (number of seconds) = duration / duration_time_base
"""
import sys
from typing import Sequence, Set

from pysaurus.core.classes import Text
from pysaurus.core.components import AbsolutePath, Duration
from pysaurus.core.functions import html_to_title, string_to_pieces
from pysaurus.database import path_utils
from pysaurus.database.semantic_text import SemanticText
from pysaurus.database.video_state import VideoState


def to_dict_value(value):
    return value.value if isinstance(value, Text) else value


class Video(VideoState):
    UNREADABLE = False

    __slots__ = (
        "audio_bit_rate",
        "audio_codec",
        "audio_codec_description",
        "bit_depth",
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
        "similarity_id",
        "_thumb_name",
        "_audio_languages",
        "_subtitle_languages",
        "video_codec",
        "video_codec_description",
        "width",
    )

    MIN_TO_LONG = {
        "A": "audio_codec_description",
        "C": "channels",
        "D": "bit_depth",
        "L": "subtitle_languages",
        "S": "similarity_id",
        "V": "video_codec_description",
        "a": "audio_codec",
        "b": "device_name",
        "c": "container_format",
        "d": "duration",
        "h": "height",
        "i": "thumb_name",
        "l": "audio_languages",
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
    assert len(LONG_TO_MIN) == len(MIN_TO_LONG)

    QUALITY_FIELDS = (
        ("quality_compression", 6),
        ("height", 5),
        ("width", 4),
        ("raw_seconds", 3),
        ("frame_rate", 2),
        ("file_size", 1),
        ("audio_bit_rate", 0.5),
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
        bit_depth=0,
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
        similarity_id=None,
        thumb_name="",
        video_codec="",
        video_codec_description="",
        width=0,
        audio_languages=None,
        subtitle_languages=None,
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
        :type bit_depth: int
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
        :type sample_rate: int
        :type similarity_id: int, optional
        :type thumb_name: str
        :type video_codec: str
        :type video_codec_description: str
        :type width: int
        :type audio_languages: list|tuple
        :type subtitle_languages: list|tuple
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
            bit_depth = from_dictionary.get(self.LONG_TO_MIN["bit_depth"], bit_depth)
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
            similarity_id = from_dictionary.get(
                self.LONG_TO_MIN["similarity_id"], similarity_id
            )
            thumb_name = from_dictionary.get(self.LONG_TO_MIN["thumb_name"], thumb_name)
            video_codec = from_dictionary.get(
                self.LONG_TO_MIN["video_codec"], video_codec
            )
            video_codec_description = from_dictionary.get(
                self.LONG_TO_MIN["video_codec_description"], video_codec_description
            )
            width = from_dictionary.get(self.LONG_TO_MIN["width"], width)
            audio_languages = from_dictionary.get(
                self.LONG_TO_MIN["audio_languages"], audio_languages
            )
            subtitle_languages = from_dictionary.get(
                self.LONG_TO_MIN["subtitle_languages"], subtitle_languages
            )
        super(Video, self).__init__(
            filename=filename,
            size=size,
            errors=errors,
            video_id=video_id,
            database=database,
            from_dictionary=from_dictionary,
        )
        self.audio_bit_rate = audio_bit_rate
        self.audio_codec = Text(audio_codec)
        self.audio_codec_description = Text(audio_codec_description)
        self.bit_depth = bit_depth
        self.channels = channels
        self.container_format = Text(container_format)
        self.device_name = Text(device_name)
        self.duration = abs(duration)
        self.duration_time_base = duration_time_base or 1
        self.frame_rate_den = frame_rate_den or 1
        self.frame_rate_num = frame_rate_num
        self.height = height
        self.meta_title = Text(html_to_title(meta_title))
        self.sample_rate = sample_rate
        self.video_codec = Text(video_codec)
        self.video_codec_description = Text(video_codec_description)
        self.width = width
        self._audio_languages = audio_languages or []
        self._subtitle_languages = subtitle_languages or []
        self._thumb_name = thumb_name  # may change when updating thumbnails
        self.similarity_id = similarity_id  # may change due to similarity search
        self.properties = {}  # may change on properties update
        # Additional initialization.
        self.set_properties(properties or {})

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
    filename_numeric = property(lambda self: SemanticText(self.filename.path))
    meta_title_numeric = property(lambda self: SemanticText(self.meta_title.value))
    raw_seconds = property(lambda self: self.duration / self.duration_time_base)
    raw_microseconds = property(
        lambda self: self.duration * 1000000 / self.duration_time_base
    )
    thumbnail_path = property(
        lambda self: path_utils.generate_thumb_path(
            self.database.thumbnail_folder, self.thumb_name
        )
    )

    @property
    def quality_compression(self):
        basic_file_size = (
            self.width * self.height * self.frame_rate * 3
            + self.sample_rate * self.channels * 2
        ) * self.raw_seconds
        return self.file_size / basic_file_size

    @property
    def quality(self):
        return self.database.quality_attribute(self)

    @property
    def move_id(self):
        return self.database.moves_attribute(self)[0]

    @property
    def moves(self):
        return [
            {"video_id": video.video_id, "filename": video.filename}
            for video in self.database.moves_attribute(self)[1]
        ]

    @property
    def thumb_name(self):
        if not self._thumb_name:
            self._thumb_name = path_utils.generate_thumb_name(self.filename)
        return self._thumb_name

    @thumb_name.setter
    def thumb_name(self, value):
        self._thumb_name = value

    @property
    def audio_languages(self):
        return self._audio_languages

    @property
    def subtitle_languages(self):
        return self._subtitle_languages

    def get_stream_languages(self):
        if (
            self._audio_languages is not None
            and None not in self._audio_languages
            and self._subtitle_languages is not None
            and None not in self._subtitle_languages
        ):
            return
        from pysaurus.database.video_info.backend_pyav import StreamsInfo

        print("[stream languages]", self.filename, file=sys.stderr)
        info = StreamsInfo.get(self.filename.path)
        self._audio_languages = [
            stream.lang_code for stream in info.audio if stream.lang_code is not None
        ]
        self._subtitle_languages = [
            stream.lang_code for stream in info.subtitle if stream.lang_code is not None
        ]

    def terms(self, as_set=False):
        term_sources = [self.filename.path, str(self.meta_title)]
        for prop in self.database.get_prop_types():
            if prop.type is str and prop.name in self.properties:
                val = self.properties[prop.name]
                if prop.multiple:
                    term_sources.extend(val)
                else:
                    term_sources.append(val)
        return string_to_pieces(" ".join(term_sources), as_set=as_set)

    @staticmethod
    def has_terms_exact(self, terms):
        # type: (Video, Sequence[str]) -> bool
        return " ".join(terms) in " ".join(self.terms())

    @staticmethod
    def has_terms_and(self, terms):
        # type: (Video, Sequence[str]) -> bool
        video_terms = self.terms(as_set=True)
        return all(term in video_terms for term in terms)

    @staticmethod
    def has_terms_or(self, terms):
        # type: (Video, Sequence[str]) -> bool
        video_terms = self.terms(as_set=True)
        return any(term in video_terms for term in terms)

    @staticmethod
    def has_terms_id(self, terms):
        # type: (Video, Sequence[str]) -> bool
        (term,) = terms
        return self.video_id == int(term)

    def set_properties(self, properties: dict) -> Set[str]:
        modified = set()
        for name, value in properties.items():
            if self.set_property(name, value):
                modified.add(name)
        return modified

    def set_property(self, name, value):
        value = self.database.get_prop_type(name)(value)
        modified = name not in self.properties or self.properties[name] != value
        self.properties[name] = value
        return modified

    def remove_property(self, name):
        self.properties.pop(name, None)

    def to_dict(self):
        dct = super().to_dict()
        len_before = len(dct)
        for _min, _long in self.MIN_TO_LONG.items():
            dct[_min] = to_dict_value(getattr(self, _long))
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
