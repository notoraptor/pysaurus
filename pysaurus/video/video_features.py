from typing import Iterable


class VideoFeatures:
    @staticmethod
    def get_common_fields(videos: Iterable, *, fields: Iterable[str], getfield=getattr):
        videos = list(videos)
        if len(videos) < 2:
            return {}
        first_video, *other_videos = videos
        return {
            key: all(
                getfield(first_video, key) == getfield(other_video, key)
                for other_video in other_videos
            )
            for key in fields
        }
