import logging
from typing import Dict, Iterable, List, Sequence, Set

from pysaurus.core.components import AbsolutePath
from pysaurus.database.abstract_video_indexer import AbstractVideoIndexer
from pysaurus.database.sql_index.video_term_index_database import VideoTermIndexDatabase
from pysaurus.database.video import Video

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


class SqlVideoIndexer(AbstractVideoIndexer):

    __slots__ = ("database",)
    TABLE = "filename_to_term"

    def __init__(self, db_path: str):
        self.database = VideoTermIndexDatabase(db_path)
        logger.info("New SQL video indexer")

    def build(self, videos: Iterable[Video]):
        for video in videos:
            self.add_video(video)

    def add_video(self, video: Video):
        if self.database.count_from_values(
            self.TABLE, "filename", filename=video.filename.path
        ):
            logger.info(f"Video already indexed: {video.filename.path}")
            return
        logger.info(f"Video indexing: {video.filename.path}")
        for term_rank, term in enumerate(video.terms()):
            self.database.insert(
                self.TABLE, filename=video.filename.path, term=term, term_rank=term_rank
            )

    def _remove_filename(self, filename: AbsolutePath, pop=False) -> List[str]:
        old_terms = []
        if pop:
            old_terms = [
                row["term"]
                for row in self.database.query(
                    "SELECT term FROM filename_to_term "
                    "WHERE filename = ? ORDER BY term_rank ASC",
                    [filename.path],
                )
            ]
        self.database.modify(
            "DELETE FROM filename_to_term WHERE filename = ?", [filename.path]
        )
        if pop:
            return old_terms

    def replace_path(self, video: Video, old_path: AbsolutePath):
        self.database.modify(
            "DELETE FROM filename_to_term WHERE filename = ?", [old_path.path]
        )
        self.add_video(video)

    def get_index(self) -> Dict[str, Set[AbsolutePath]]:
        index = {}
        for row in self.database.query(
            "SELECT filename, term FROM filename_to_term "
            "ORDER BY filename ASC, term_rank ASC"
        ):
            index.setdefault(AbsolutePath(row["filename"]), []).append(row["term"])
        return index

    def _term_to_filenames(self, term: str) -> Iterable[AbsolutePath]:
        return (
            AbsolutePath(row["filename"])
            for row in self.database.query(
                "SELECT filename FROM filename_to_term WHERE term = ?", [term]
            )
        )

    def query_and(
        self, filenames: Iterable[AbsolutePath], terms: Sequence[str]
    ) -> Iterable[AbsolutePath]:
        return set.intersection(
            set(filenames), *(set(self._term_to_filenames(term)) for term in terms)
        )

    def query_exact(
        self, filenames: Iterable[AbsolutePath], terms: Sequence[str]
    ) -> Iterable[AbsolutePath]:
        selection = set()
        filenames = set(filenames)
        first_term, *other_terms = terms
        for row in self.database.query_all(
            "SELECT filename, term_rank FROM filename_to_term WHERE term = ?",
            [first_term],
        ):
            filename = AbsolutePath(row["filename"])
            term_rank = row["term_rank"]
            if filename in filenames:
                found = True
                for i, other_term in enumerate(other_terms):
                    if not self.database.count_from_values(
                        self.TABLE,
                        "filename",
                        filename=filename.path,
                        term=other_term,
                        term_rank=term_rank + i + 1,
                    ):
                        found = False
                        break
                if found:
                    selection.add(filename)
        return selection

    def query_or(
        self, filenames: Iterable[AbsolutePath], terms: Sequence[str]
    ) -> Iterable[AbsolutePath]:
        return set(filenames) & set.union(
            *(set(self._term_to_filenames(term)) for term in terms)
        )
