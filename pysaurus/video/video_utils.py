from typing import Iterable, List

from pysaurus.video import Video
from pysaurus.video.tag import Tag, Term


def video_to_tags(video: Video) -> List[Tag]:
    return video.terms() + [Tag(flag, getattr(video, flag)) for flag in VIDEO_FLAGS]


def terms_to_tags(terms: Iterable[str], cls=set) -> Iterable[Term]:
    return cls(Term(term) for term in terms)


def terms_to_string(tags: Iterable[Tag], sep=" ") -> str:
    return sep.join(tag.val for tag in tags if isinstance(tag, Term))


VIDEO_FLAGS = {
    "readable",
    "unreadable",
    "found",
    "not_found",
    "with_thumbnails",
    "without_thumbnails",
    "discarded",
}
COMMON_FIELDS = (
    "audio_bit_rate",
    "audio_bits",
    "audio_codec",
    "audio_codec_description",
    "audio_languages",
    "bit_depth",
    "channels",
    "container_format",
    "date",
    "date_entry_modified",
    "date_entry_opened",
    "errors",
    "file_size",
    "filename",
    "frame_rate",
    "height",
    "length",
    "sample_rate",
    "similarity_id",
    "subtitle_languages",
    "video_codec",
    "video_codec_description",
    "width",
    "extension",
    "size",
    "bit_rate",
)
