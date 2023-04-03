from typing import Iterable, List

from pysaurus.video import Video
from pysaurus.video.tag import Tag, Term


def video_to_tags(video: Video) -> List[Tag]:
    return video.terms() + [Tag(flag, getattr(video, flag)) for flag in Video.FLAGS]


def terms_to_tags(terms: Iterable[str], cls=set) -> Iterable[Term]:
    return cls(Term(term) for term in terms)


def terms_to_string(tags: Iterable[Tag], sep=" ") -> str:
    return sep.join(tag.val for tag in tags if isinstance(tag, Term))
