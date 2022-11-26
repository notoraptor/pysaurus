from typing import Dict, Iterable, List, Sequence, Set

from pysaurus.core.components import AbsolutePath
from pysaurus.core.functions import string_to_pieces
from pysaurus.database.video import Video


class VideoIndexer:
    __slots__ = ("term_to_filenames", "filename_to_terms")

    def __init__(self):
        self.term_to_filenames: Dict[str, Set[AbsolutePath]] = {}
        self.filename_to_terms: Dict[AbsolutePath, List[str]] = {}

    def build(self, videos: Iterable[Video]):
        self.term_to_filenames.clear()
        self.filename_to_terms.clear()
        for video in videos:
            self.add_video(video)

    def add_video(self, video: Video):
        terms = video.terms()
        self.filename_to_terms[video.filename] = terms
        for term in terms:
            self.term_to_filenames.setdefault(term, set()).add(video.filename)

    def remove_video(self, video: Video):
        self._remove_filename(video.filename)

    def _remove_filename(self, filename: AbsolutePath) -> List[str]:
        old_terms = self.filename_to_terms.pop(filename)
        for term in old_terms:
            self._remove_term_to_filename(term, filename)
        return old_terms

    def _remove_term_to_filename(self, term: str, filename: AbsolutePath):
        if term in self.term_to_filenames and filename in self.term_to_filenames[term]:
            self.term_to_filenames[term].remove(filename)
            if not self.term_to_filenames[term]:
                del self.term_to_filenames[term]

    def update_video(self, video: Video):
        self.remove_video(video)
        self.add_video(video)

    def replace_path(self, video: Video, old_path: AbsolutePath):
        all_old_terms = self._remove_filename(old_path)
        old_terms = string_to_pieces(str(old_path), as_set=True)
        new_terms = string_to_pieces(str(video.filename), as_set=True)
        pure_old_terms = old_terms - new_terms
        pure_new_terms = new_terms - old_terms
        self.filename_to_terms[video.filename] = list(
            (set(all_old_terms) - pure_old_terms) | pure_new_terms
        )
        for new_term in self.filename_to_terms[video.filename]:
            self.term_to_filenames.setdefault(new_term, set()).add(video.filename)

    def get_index(self) -> Dict[str, Set[AbsolutePath]]:
        return self.term_to_filenames

    def filename_has_terms_exact(self, filename: AbsolutePath, terms: Sequence[str]):
        return " ".join(terms) in " ".join(self.filename_to_terms[filename])
