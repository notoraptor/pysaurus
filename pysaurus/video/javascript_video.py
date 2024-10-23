"""
Match:
saurus.sql.sql_video_wrapper.SQLVideoWrapper.json
pysaurus.database.jsdb.jsdbvideo.json_video_features.JsonVideoFeatures.json
"""

from typing import List, Optional


class JavascriptVideo:
    """
    Wrapper around video data returned by AbstractDatabase.get_videos()
    when called with argument `include=None`.

    Video data is a dict whose values are Javascript-compatible.
    Because of that, value types in this dict don't necessarily match
    Python types of associated values in Python video objects.
    """

    __slots__ = ("data",)

    def __init__(self, data: dict):
        self.data = data

    @property
    def audio_bit_rate(self) -> int:
        return self.data["audio_bit_rate"]

    @property
    def audio_bits(self) -> int:
        return self.data["audio_bits"]

    @property
    def audio_codec(self) -> str:
        return self.data["audio_codec"]

    @property
    def audio_codec_description(self) -> str:
        return self.data["audio_codec_description"]

    @property
    def audio_languages(self) -> List[str]:
        return self.data["audio_languages"]

    @property
    def bit_depth(self) -> int:
        return self.data["bit_depth"]

    @property
    def bit_rate(self) -> float:
        return self.data["bit_rate"]

    @property
    def channels(self) -> int:
        return self.data["channels"]

    @property
    def container_format(self) -> str:
        return self.data["container_format"]

    @property
    def date(self) -> str:
        return self.data["date"]

    @property
    def date_entry_modified(self) -> str:
        return self.data["date_entry_modified"]

    @property
    def date_entry_opened(self) -> str:
        return self.data["date_entry_opened"]

    @property
    def errors(self) -> List[str]:
        return self.data["errors"]

    @property
    def extension(self) -> str:
        return self.data["extension"]

    @property
    def file_size(self) -> int:
        return self.data["file_size"]

    @property
    def file_title(self) -> str:
        return self.data["file_title"]

    @property
    def filename(self) -> str:
        return self.data["filename"]

    @property
    def found(self) -> bool:
        return self.data["found"]

    @property
    def frame_rate(self) -> float:
        return self.data["frame_rate"]

    @property
    def height(self) -> int:
        return self.data["height"]

    @property
    def length(self) -> str:
        return self.data["length"]

    @property
    def moves(self) -> Optional[List[dict]]:
        return self.data["moves"]

    @property
    def properties(self) -> dict:
        return self.data["properties"]

    @property
    def readable(self) -> bool:
        return self.data["readable"]

    @property
    def sample_rate(self) -> int:
        return self.data["sample_rate"]

    @property
    def similarity_id(self) -> int:
        return self.data["similarity_id"]

    @property
    def size(self) -> str:
        return self.data["size"]

    @property
    def subtitle_languages(self) -> List[str]:
        return self.data["subtitle_languages"]

    @property
    def thumbnail_path(self) -> Optional[str]:
        return self.data["thumbnail_path"]

    @property
    def thumbnail_base64(self) -> Optional[str]:
        return self.data["thumbnail_base64"]

    @property
    def title(self) -> str:
        return self.data["title"]

    @property
    def video_codec(self) -> str:
        return self.data["video_codec"]

    @property
    def video_codec_description(self) -> str:
        return self.data["video_codec_description"]

    @property
    def video_id(self) -> int:
        return self.data["video_id"]

    @property
    def width(self) -> int:
        return self.data["width"]

    @property
    def with_thumbnails(self) -> bool:
        return self.data["with_thumbnails"]
