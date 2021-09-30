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

    @staticmethod
    def get_common_fields(videos: Iterable[Video]):
        videos = list(videos)
        if len(videos) < 2:
            return {}
        types = set(type(video) for video in videos)
        common_attributes = set.intersection(
            *(class_get_public_attributes(typ, wrapper=set) for typ in types)
        )
        first_video, *other_videos = videos
        return {
            key: all(
                getattr(first_video, key) == getattr(other_video, key)
                for other_video in other_videos
            )
            for key in common_attributes
        }
