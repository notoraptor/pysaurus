from typing import Iterable, Dict, Set, List
from pysaurus.database.video import Video
from pysaurus.core.functions import string_to_pieces
from pysaurus.core.components import AbsolutePath


class VideoIndexer:
    # __slots__ = ()

    def __init__(self):
        self.term_to_videos: Dict[str, Set[Video]] = {}
        self.video_to_terms: Dict[AbsolutePath, List[str]] = {}

    def build(self, videos: Iterable[Video]):
        self.term_to_videos.clear()
        self.video_to_terms.clear()
        for video in videos:
            self.add_video(video)

    def add_video(self, video: Video):
        terms = video.terms()
        self.video_to_terms[video.filename] = terms
        for term in terms:
            self.term_to_videos.setdefault(term, set()).add(video)

    def remove_video(self, video: Video):
        for term in self.video_to_terms.pop(video.filename):
            self._remove_term_to_video(term, video)

    def _remove_term_to_video(self, term, video):
        if term in self.term_to_videos and video in self.term_to_videos[term]:
            self.term_to_videos[term].remove(video)
            if not self.term_to_videos[term]:
                del self.term_to_videos[term]

    def update_video(self, video: Video):
        self.remove_video(video)
        self.add_video(video)

    def replace_path(self, video: Video, old_path: AbsolutePath):
        old_terms = string_to_pieces(str(old_path), as_set=True)
        new_terms = string_to_pieces(str(video.filename), as_set=True)
        pure_old_terms = old_terms - new_terms
        pure_new_terms = new_terms - old_terms
        self.video_to_terms[video.filename] = list(
            (set(self.video_to_terms[old_path]) - pure_old_terms) | pure_new_terms
        )
        for old_term in pure_old_terms:
            self._remove_term_to_video(old_term, video)
        for new_term in pure_new_terms:
            self.term_to_videos.setdefault(new_term, set()).add(video)

    def get_index(self) -> Dict[str, Set[Video]]:
        return self.term_to_videos
