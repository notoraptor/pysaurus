from typing import Iterable, Sequence

from pysaurus.core.functions import class_get_public_attributes, to_json_value
from pysaurus.video import Video

VIDEO_FIELDS = class_get_public_attributes(Video)


class VideoFeatures:
    @staticmethod
    def to_json(self):
        return {field: to_json_value(getattr(self, field)) for field in VIDEO_FIELDS}

    @staticmethod
    def has_terms_exact(self: Video, terms: Sequence[str]) -> bool:
        return " ".join(terms) in " ".join(self.terms())

    @staticmethod
    def has_terms_and(self: Video, terms: Sequence[str]) -> bool:
        video_terms = self.terms(as_set=True)
        return all(term in video_terms for term in terms)

    @staticmethod
    def has_terms_or(self: Video, terms: Sequence[str]) -> bool:
        video_terms = self.terms(as_set=True)
        return any(term in video_terms for term in terms)

    @staticmethod
    def has_terms_id(self: Video, terms: Sequence[str]) -> bool:
        (term,) = terms
        return self.video_id == int(term)

    @staticmethod
    def get_common_fields(videos: Iterable[Video]):
        videos = list(videos)
        if len(videos) < 2:
            return {}
        first_video, *other_videos = videos
        return {
            key: all(
                getattr(first_video, key) == getattr(other_video, key)
                for other_video in other_videos
            )
            for key in VIDEO_FIELDS
        }
