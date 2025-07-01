from typing import Iterable

from pysaurus.database.jsdb.jsdbvideo.lazy_video import LazyVideo as Video
from pysaurus.database.jsdb.jsdbvideo.tag import Tag, Term
from pysaurus.video.video_constants import VIDEO_FLAGS


def video_to_tags(video: Video) -> list[Tag]:
    return video.terms() + [Tag(flag, getattr(video, flag)) for flag in VIDEO_FLAGS]


def terms_to_tags(terms: Iterable[str], cls=set) -> Iterable[Term]:
    return cls(Term(term) for term in terms)


def terms_to_string(tags: Iterable[Tag], sep=" ") -> str:
    return sep.join(tag.val for tag in tags if isinstance(tag, Term))
