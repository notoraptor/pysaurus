from typing import Dict, Iterable, List, Sequence, Set

from pysaurus.core.components import AbsolutePath
from pysaurus.core.job_notifications import (
    global_notify_job_progress,
    global_notify_job_start,
)
from pysaurus.video import Video
from pysaurus.video.abstract_video_indexer import AbstractVideoIndexer
from pysaurus.video.tag import Tag
from pysaurus.video.video_utils import terms_to_tags, video_to_tags

EMPTY_SET = set()


class VideoIndexer(AbstractVideoIndexer):
    __slots__ = ("term_to_filenames", "filename_to_terms")

    def __init__(self):
        self.term_to_filenames: Dict[Tag, Set[AbsolutePath]] = {}
        self.filename_to_terms: Dict[AbsolutePath, List[Tag]] = {}

    def build(self, videos: Iterable[Video]):
        self.filename_to_terms = {
            video.filename: video_to_tags(video) for video in videos
        }
        nb_videos = len(self.filename_to_terms)
        global_notify_job_start("build_index", nb_videos, "videos")
        self.term_to_filenames.clear()
        for i, (filename, terms) in enumerate(self.filename_to_terms.items()):
            for term in terms:
                self.term_to_filenames.setdefault(term, set()).add(filename)
            if (i + 1) % 500 == 0:
                global_notify_job_progress("build_index", None, i + 1, nb_videos)
        global_notify_job_progress("build_index", None, nb_videos, nb_videos)

    def add_video(self, video: Video):
        terms = video_to_tags(video)
        self.filename_to_terms[video.filename] = terms
        for term in terms:
            self.term_to_filenames.setdefault(term, set()).add(video.filename)

    def _remove_filename(self, filename: AbsolutePath) -> None:
        for term in self.filename_to_terms.pop(filename, []):
            if (
                term in self.term_to_filenames
                and filename in self.term_to_filenames[term]
            ):
                self.term_to_filenames[term].remove(filename)
                if not self.term_to_filenames[term]:
                    del self.term_to_filenames[term]

    def replace_path(self, video: Video, old_path: AbsolutePath):
        self._remove_filename(old_path)
        self.add_video(video)

    def update_videos(self, videos: Iterable[Video]):
        for video in videos:
            self._update_video(video)

    def _update_video(self, video: Video):
        new_terms = video_to_tags(video)
        old_terms = self.filename_to_terms.pop(video.filename, ())
        self.filename_to_terms[video.filename] = new_terms
        set_new_terms = set(new_terms)
        common_terms = set()
        for old_term in old_terms:
            if old_term in set_new_terms:
                common_terms.add(old_term)
            elif (
                old_term in self.term_to_filenames
                and video.filename in self.term_to_filenames[old_term]
            ):
                self.term_to_filenames[old_term].remove(video.filename)
                if not self.term_to_filenames[old_term]:
                    del self.term_to_filenames[old_term]
        for pure_new_term in set_new_terms - common_terms:
            self.term_to_filenames.setdefault(pure_new_term, set()).add(video.filename)

    def query_and(
        self, filenames: Iterable[AbsolutePath], terms: Sequence[str]
    ) -> Set[AbsolutePath]:
        terms = terms_to_tags(terms, cls=list)
        return set.intersection(
            set(filenames),
            *(self.term_to_filenames.get(term, EMPTY_SET) for term in terms),
        )

    def query_or(
        self, filenames: Iterable[AbsolutePath], terms: Sequence[str]
    ) -> Set[AbsolutePath]:
        terms = terms_to_tags(terms, cls=list)
        return set(filenames) & set.union(
            *(self.term_to_filenames.get(term, EMPTY_SET) for term in terms)
        )
