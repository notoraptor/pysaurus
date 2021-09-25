from typing import Iterable

from pysaurus.core import functions
from pysaurus.core.functions import to_json_value, class_get_public_attributes
from pysaurus.database.video import Video
from pysaurus.database.viewport.viewtools.search_def import SearchDef


class VideoFeatures:

    @staticmethod
    def to_json(self, **kwargs):
        js = {
            field: to_json_value(getattr(self, field))
            for field in class_get_public_attributes(type(self))
        }
        js.update(kwargs)
        return js

    @staticmethod
    def find(search: SearchDef, videos: Iterable[Video]) -> Iterable[Video]:
        terms = functions.string_to_pieces(search.text)
        video_filter = getattr(Video, f"has_terms_{search.cond}")
        return (video for video in videos if video_filter(video, terms))
