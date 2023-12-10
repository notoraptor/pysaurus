from dataclasses import dataclass, field
from typing import Dict, Sequence

from saurus.sql.video_entry import VideoEntry


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
class Collection:
    name: str
    date_updated: float
    miniature_pixel_dst_radius: int = 6
    miniature_group_min_size: int = 0
    sources: Sequence[str] = field(default_factory=list)
    properties: Dict[str, Property] = field(default_factory=dict)
    videos: Dict[str, VideoEntry] = field(default_factory=dict)
    collection_id: int = None
