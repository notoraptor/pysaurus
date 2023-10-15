from dataclasses import dataclass, field
from typing import Dict, Sequence


@dataclass
class Property:
    name: str
    type: str
    default_value: str = None
    enumeration: Sequence[str] = field(default_factory=list)
    property_id: int = None

    @property
    def multiple(self):
        return self.default_value is None


@dataclass
class Video:
    # table columns: constant data
    video_id: int
    filename: str
    file_size: int = 0
    readable: bool = False
    audio_bit_rate: int = 0
    audio_codec: str = ""
    audio_codec_description: str = ""
    bit_depth: int = 0
    channels: int = 2
    container_format: str = ""
    device_name: str = ""
    duration: int = 0
    duration_time_base: int = 0
    frame_rate_den: int = 0
    frame_rate_num: int = 0
    height: int = 0
    meta_title: str = ""
    sample_rate: int = 0
    video_codec: str = ""
    video_codec_description: str = ""
    width: int = 0
    # table columns: runtime frozen data
    mtime: float = 0.0
    driver_id: int = 0
    is_file: bool = False
    # related data
    errors: Sequence[str] = field(default_factory=list)
    audio_languages: Sequence[str] = field(default_factory=list)
    subtitle_languages: Sequence[str] = field(default_factory=list)
    # collection data
    thumb_name: str = ""
    similarity_id: int = None
    properties: Dict[str, Sequence[str]] = field(default_factory=dict)


@dataclass
class Collection:
    name: str
    date_updated: float
    miniature_pixel_dst_radius: int = 6
    miniature_group_min_size: int = 0
    sources: Sequence[str] = field(default_factory=list)
    properties: Dict[str, Property] = field(default_factory=dict)
    videos: Dict[str, Video] = field(default_factory=dict)
    collection_id: int = None
