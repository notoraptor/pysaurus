import logging
import os
from typing import Dict, Iterable, List, Sequence, Set

from pysaurus.core.components import AbsolutePath
from pysaurus.core.job_notifications import (
    global_notify_job_progress,
    global_notify_job_start,
)
from pysaurus.database.abstract_video_indexer import AbstractVideoIndexer
from pysaurus.database.sql_index.video_term_index_database import VideoTermIndexDatabase
from pysaurus.database.video import Video

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


class SqlVideoIndexer(AbstractVideoIndexer):

    __slots__ = ("database", "_to_build")

    def __init__(self, db_path: str):
        self._to_build = not os.path.exists(db_path)
        self.database = VideoTermIndexDatabase(db_path)
        logger.info("New SQL video indexer")

    def build(self, videos: Iterable[Video]):
        if self._to_build:
            all_filenames = []
            filename_id_to_terms = []
            unique_terms = set()
            for video in videos:
                video_terms = video.terms()
                all_filenames.append(video.filename.path)
                filename_id_to_terms.append(video_terms)
                unique_terms.update(video_terms)
            global_notify_job_start("sql_build_index", len(all_filenames), "videos")
            all_terms = sorted(unique_terms)
            term_to_id = {term: term_id for term_id, term in enumerate(all_terms)}
            self.database.modify(
                "INSERT INTO filename (filename_id, filename) " "VALUES (?, ?)",
                enumerate(all_filenames),
                many=True,
            )
            self.database.modify(
                "INSERT INTO term (term_id, term) VALUES (?, ?)",
                enumerate(all_terms),
                many=True,
            )
            for (filename_id, terms) in enumerate(filename_id_to_terms):
                global_notify_job_progress(
                    "sql_build_index", None, filename_id + 1, len(all_filenames)
                )
                self.database.modify(
                    "INSERT INTO filename_to_term (filename_id, term_id, term_rank) "
                    "VALUES (?, ?, ?)",
                    (
                        (filename_id, term_to_id[term], term_rank)
                        for term_rank, term in enumerate(terms)
                    ),
                    many=True,
                )
            self._to_build = False

    def add_video(self, video: Video):
        logger.info(f"Video indexing: {video.filename.path}")
        filename_id = self.database.select_id_from_values(
            "filename", "filename_id", filename=video.filename.path
        ) or self.database.modify(
            "INSERT INTO filename (filename) VALUES (?)", [video.filename.path]
        )
        for term_rank, term in enumerate(video.terms()):
            term_id = self.database.select_id_from_values(
                "term", "term_id", term=term
            ) or self.database.insert("term", term=term)
            self.database.insert_or_ignore(
                "filename_to_term",
                filename_id=filename_id,
                term_id=term_id,
                term_rank=term_rank,
            )

    def _remove_filename(self, filename: AbsolutePath, pop=False) -> List[str]:
        old_terms = []
        if pop:
            old_terms = [
                row["term"]
                for row in self.database.query(
                    "SELECT t.term FROM term AS t "
                    "JOIN filename_to_term AS j ON t.term_id = j.term_id "
                    "JOIN filename AS f ON j.filename_id = f.filename_id "
                    "WHERE f.filename = ? "
                    "ORDER BY t.term_rank ASC",
                    [filename.path],
                )
            ]
        self.database.modify("DELETE FROM filename WHERE filename = ?", [filename.path])
        if pop:
            return old_terms

    def replace_path(self, video: Video, old_path: AbsolutePath):
        self.database.modify("DELETE FROM filename WHERE filename = ?", [old_path.path])
        self.add_video(video)

    def get_index(self) -> Dict[str, Set[AbsolutePath]]:
        index = {}
        for row in self.database.query(
            "SELECT f.filename, t.term FROM filename AS f "
            "JOIN filename_to_term AS j ON f.filename_id = j.filename_id "
            "JOIN term AS t ON j.term_id = t.term_id "
            "ORDER BY f.filename ASC, t.term_rank ASC"
        ):
            index.setdefault(AbsolutePath(row["filename"]), []).append(row["term"])
        return index

    def _term_to_filenames(self, term: str) -> Iterable[AbsolutePath]:
        return (
            AbsolutePath(row["filename"])
            for row in self.database.query(
                "SELECT f.filename AS filename FROM filename AS f "
                "JOIN filename_to_term AS j ON f.filename_id = j.filename_id "
                "JOIN term AS t ON j.term_id = t.term_id "
                "WHERE t.term = ?",
                [term],
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
            "SELECT f.filename AS filename, j.term_rank AS term_rank "
            "FROM filename AS f "
            "JOIN filename_to_term AS j ON f.filename_id = j.filename_id "
            "JOIN term AS t ON j.term_id = t.term_id "
            "WHERE t.term = ?",
            [first_term],
        ):
            filename = AbsolutePath(row["filename"])
            term_rank = row["term_rank"]
            if filename in filenames:
                found = True
                for i, other_term in enumerate(other_terms):
                    row_count = self.database.query_one(
                        "SELECT COUNT(j.filename_id) AS count "
                        "FROM filename AS f "
                        "JOIN filename_to_term AS j ON f.filename_id = j.filename_id "
                        "JOIN term AS t ON j.term_id = t.term_id "
                        "WHERE f.filename = ? AND t.term = ? AND j.term_rank = ?",
                        [filename.path, other_term, term_rank + i + 1],
                    )
                    if not row_count["count"]:
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
