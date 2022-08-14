"""
Video class. Properties:

- length: Return a Duration object representing the video duration.
  Based on raw duration fields `duration` and `duration_time_base`, we have: ::

    duration = (number of seconds) * duration_time_base

  So: ::

    (number of seconds) = duration / duration_time_base
"""
from typing import Any, Dict, Iterable, Sequence, Set

from pysaurus.core.classes import Text
from pysaurus.core.components import Duration
from pysaurus.core.functions import html_to_title, string_to_pieces
from pysaurus.database import db_utils
from pysaurus.database.semantic_text import SemanticText
from pysaurus.database.video_state import VideoState


class Video(VideoState):
    unreadable: "U" = False
    # Video optional arguments
    audio_bit_rate: "r" = 0
    audio_codec: "a" = ""
    audio_codec_description: "A" = ""
    bit_depth: "D" = 0
    channels: "C" = 2
    container_format: "c" = ""
    device_name: "b" = ""
    duration: "d" = 0.0
    duration_time_base: "t" = 0
    frame_rate_den: "y" = 0
    frame_rate_num: "x" = 0
    height: "h" = 0
    meta_title: "n" = ""
    properties: "p" = {}
    sample_rate: "u" = 0
    similarity_id: ("S", int) = None
    video_codec: "v" = ""
    video_codec_description: "V" = ""
    width: "w" = 0
    audio_languages: "l" = []
    subtitle_languages: "L" = []

    __slots__ = ("database",)

    def __init__(self, database, **kwargs):
        super().__init__(**kwargs)
        self.__json__["duration"] = abs(self.__json__["duration"])
        self.__json__["duration_time_base"] = self.__json__["duration_time_base"] or 1
        self.__json__["frame_rate_den"] = self.__json__["frame_rate_den"] or 1
        # Runtime
        self.database = database
        # Additional initialization.
        self.update_properties(self.__json__["properties"])

    def get_audio_codec(self):
        return Text(self.__json__["audio_codec"])

    def get_audio_codec_description(self):
        return Text(self.__json__["audio_codec_description"])

    def get_container_format(self):
        return Text(self.__json__["container_format"])

    def get_device_name(self):
        return Text(self.__json__["device_name"])

    def get_meta_title(self):
        return Text(html_to_title(self.__json__["meta_title"]))

    def get_video_codec(self):
        return Text(self.__json__["video_codec"])

    def get_video_codec_description(self):
        return Text(self.__json__["video_codec_description"])

    def get_thumb_name(self):
        thumb_name = self.__json__["thumb_name"]
        if not thumb_name:
            thumb_name = db_utils.generate_thumb_name(self.filename)
            self.__json__["thumb_name"] = thumb_name
        return thumb_name

    def set_properties(self, properties: dict):
        self.__json__["properties"] = {
            key: self.database.get_prop_type(key)(value)
            for key, value in properties.items()
        }

    def extract_attributes(self, keys: Iterable[str]) -> Dict[str, Any]:
        output = {}
        for key in keys:
            if key.startswith(":"):
                prop_name = key[1:]
                output.setdefault("properties", {})[prop_name] = self.properties[
                    prop_name
                ]
            else:
                output[key] = getattr(self, key)
        return output

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
        lambda self: db_utils.generate_thumb_path(
            self.database.thumbnail_folder, self.thumb_name
        )
    )
    quality = property(lambda self: self.database.quality_attribute(self))
    move_id = property(lambda self: self.database.moves_attribute(self)[0])

    @property
    def quality_compression(self):
        basic_file_size = (
            self.width * self.height * self.frame_rate * 3
            + self.sample_rate * self.channels * 2
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

    def update_properties(self, properties: dict) -> Set[str]:
        modified = set()
        for name, value in properties.items():
            if self.update_property(name, value):
                modified.add(name)
        return modified

    def update_property(self, name, value):
        value = self.database.get_prop_type(name)(value)
        modified = name not in self.properties or self.properties[name] != value
        self.properties[name] = value
        return modified

    def remove_property(self, name):
        self.properties.pop(name, None)
