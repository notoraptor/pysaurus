import pickle
from typing import Dict, Iterable, List, Sequence, Set

from pysaurus.core.components import AbsolutePath
from pysaurus.core.informer import Informer
from pysaurus.core.notifying import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.profiling import Profiler
from pysaurus.video import Video
from pysaurus.video.abstract_video_indexer import AbstractVideoIndexer
from pysaurus.video.tag import Tag
from pysaurus.video.video_utils import video_to_tags

EMPTY_SET = set()


class VideoIndexer(AbstractVideoIndexer):
    __slots__ = (
        "term_to_filenames",
        "filename_to_terms",
        "notifier",
        "built",
        "index_path",
    )

    def __init__(
        self, notifier: Notifier = DEFAULT_NOTIFIER, index_path: AbsolutePath = None
    ):
        self.notifier = notifier
        self.term_to_filenames: Dict[Tag, Set[str]] = {}
        self.filename_to_terms: Dict[str, List[Tag]] = {}
        self.built = False
        self.index_path = index_path

    def _can_save(self) -> bool:
        return True

    @Profiler.profile_method("VideoIndexer.save")
    def _save(self):
        with open(self.index_path.path, "wb") as file:
            pickle.dump(
                (self.term_to_filenames, self.filename_to_terms, self.built), file
            )

    @Profiler.profile_method("VideoIndexer.load")
    def _load(self):
        with open(self.index_path.path, "rb") as file:
            self.term_to_filenames, self.filename_to_terms, self.built = pickle.load(
                file
            )

    @Profiler.profile_method("indexer_build")
    def build(self, videos: Iterable[Video]):
        notifier = Informer.default()
        if self.index_path and self.index_path.isfile():
            self._load()
        videos = [
            video
            for video in videos
            if video.filename.path not in self.filename_to_terms
        ]
        if self.built and not videos:
            return

        self.filename_to_terms = {
            video.filename.path: video_to_tags(video) for video in videos
        }
        nb_videos = len(self.filename_to_terms)
        notifier.task("build_index", nb_videos, "videos")
        self.term_to_filenames.clear()
        for i, (filename, terms) in enumerate(self.filename_to_terms.items()):
            for term in terms:
                self.term_to_filenames.setdefault(term, set()).add(filename)
            if (i + 1) % 500 == 0:
                notifier.progress("build_index", i + 1, nb_videos)
        notifier.progress("build_index", nb_videos, nb_videos)
        self.built = True

        self._save()

    def _add_video(self, video: Video):
        terms = video_to_tags(video)
        self.filename_to_terms[video.filename.path] = terms
        for term in terms:
            self.term_to_filenames.setdefault(term, set()).add(video.filename.path)

    def _remove_filename(self, filename: AbsolutePath) -> None:
        filename = filename.path
        for term in self.filename_to_terms.pop(filename, []):
            if (
                term in self.term_to_filenames
                and filename in self.term_to_filenames[term]
            ):
                self.term_to_filenames[term].remove(filename)
                if not self.term_to_filenames[term]:
                    del self.term_to_filenames[term]

    def _update_video(self, video: Video):
        new_terms = video_to_tags(video)
        old_terms = self.filename_to_terms.pop(video.filename.path, ())
        self.filename_to_terms[video.filename.path] = new_terms
        set_new_terms = set(new_terms)
        common_terms = set()
        for old_term in old_terms:
            if old_term in set_new_terms:
                common_terms.add(old_term)
            elif (
                old_term in self.term_to_filenames
                and video.filename.path in self.term_to_filenames[old_term]
            ):
                self.term_to_filenames[old_term].remove(video.filename.path)
                if not self.term_to_filenames[old_term]:
                    del self.term_to_filenames[old_term]
        for pure_new_term in set_new_terms - common_terms:
            self.term_to_filenames.setdefault(pure_new_term, set()).add(
                video.filename.path
            )

    def indexed_videos(self, videos: Iterable[Video]) -> Sequence[Video]:
        return [
            video for video in videos if video.filename.path in self.filename_to_terms
        ]

    @Profiler.profile_method()
    def query_and(
        self, filenames: Iterable[AbsolutePath], terms: Sequence[str]
    ) -> Set[AbsolutePath]:
        # terms = terms_to_tags(terms, cls=list)
        base = {filename.path for filename in filenames}
        return AbsolutePath.map(
            set.intersection(
                base, *(self.term_to_filenames.get(term, EMPTY_SET) for term in terms)
            )
        )

    @Profiler.profile_method()
    def query_or(
        self, filenames: Iterable[AbsolutePath], terms: Sequence[str]
    ) -> Set[AbsolutePath]:
        # terms = terms_to_tags(terms, cls=list)
        base = {filename.path for filename in filenames}
        return AbsolutePath.map(
            base
            & set.union(
                *(self.term_to_filenames.get(term, EMPTY_SET) for term in terms)
            )
        )

    @Profiler.profile_method()
    def query_flags(
        self, filenames: Iterable[AbsolutePath], *flags, **forced_flags
    ) -> Iterable[AbsolutePath]:
        required = {flag: True for flag in flags}
        required.update(forced_flags)
        required["discarded"] = required.get("discarded", False)
        terms = [Tag(flag, value) for flag, value in required.items()]
        base = {filename.path for filename in filenames}
        return AbsolutePath.map(
            set.intersection(
                base, *(self.term_to_filenames.get(term, EMPTY_SET) for term in terms)
            )
        )
