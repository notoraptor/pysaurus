from dataclasses import dataclass

from pysaurus.core.components import AbsolutePath
from pysaurus.video.video_search_context import VideoSearchContext


@dataclass(slots=True)
class DatabaseContext:
    name: str
    folders: list[AbsolutePath]
    prop_types: list[dict]
    view: VideoSearchContext
