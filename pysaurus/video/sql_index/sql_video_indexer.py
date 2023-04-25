import logging
import os
from typing import Iterable, Sequence

from pysaurus.core.components import AbsolutePath
from pysaurus.core.job_notifications import (
    global_notify_job_progress,
    global_notify_job_start,
)
from pysaurus.video import Video
from pysaurus.video.abstract_video_indexer import AbstractVideoIndexer
from pysaurus.video.sql_index.video_term_index_database import VideoTermIndexDatabase

logger = logging.getLogger(__name__)


class SqlVideoIndexer(AbstractVideoIndexer):
    __slots__ = ("sql_database", "_to_build")

    def __init__(self, db_path: str):
        self._to_build = not os.path.exists(db_path)
        self.sql_database = VideoTermIndexDatabase(db_path)
        logger.info("New SQL video indexer")

    def build(self, videos: Iterable[Video]):
        if self._to_build:
            filename_and_terms = [
                (video.filename.path, video.terms()) for video in videos
            ]

            all_terms = sorted(
                set.union(*(set(couple[1]) for couple in filename_and_terms))
            )
            term_to_id = {term: term_id for term_id, term in enumerate(all_terms)}
            self.sql_database.modify(
                "INSERT INTO filename (filename_id, filename) " "VALUES (?, ?)",
                enumerate(couple[0] for couple in filename_and_terms),
                many=True,
            )
            self.sql_database.modify(
                "INSERT INTO term (term_id, term) VALUES (?, ?)",
                enumerate(all_terms),
                many=True,
            )

            nb_filenames = len(filename_and_terms)
            step = 500
            total = 0
            global_notify_job_start("sql_build_index", nb_filenames, "videos")
            for start in range(0, nb_filenames, step):
                limit = min(start + step, nb_filenames)
                total += limit - start
                self.sql_database.modify(
                    "INSERT INTO filename_to_term (filename_id, term_id, term_rank) "
                    "VALUES (?, ?, ?)",
                    (
                        (filename_id, term_to_id[term], term_rank)
                        for filename_id in range(start, limit)
                        for term_rank, term in enumerate(
                            filename_and_terms[filename_id][1]
                        )
                    ),
                    many=True,
                )
                global_notify_job_progress("sql_build_index", None, limit, nb_filenames)
            assert nb_filenames == total
            global_notify_job_progress(
                "sql_build_index", None, nb_filenames, nb_filenames
            )
            self._to_build = False

    def update_videos(self, videos: Iterable[Video]):
        filename_and_terms = [(video.filename.path, video.terms()) for video in videos]
        logger.info(f"Indexing {len(filename_and_terms)} video(s).")
        # Delete videos
        self.sql_database.modify(
            "DELETE FROM filename WHERE filename = ?",
            ([couple[0]] for couple in filename_and_terms),
            many=True,
        )
        # Then re-insert new videos
        last_fid = self.sql_database.query_one(
            "SELECT MAX(filename_id) AS last_id FROM filename"
        )["last_id"]
        next_f_indices = list(
            range(last_fid + 1, last_fid + 1 + len(filename_and_terms))
        )
        self.sql_database.modify(
            "INSERT INTO filename (filename_id, filename) VALUES (?, ?)",
            (
                (filename_id, filename)
                for filename_id, (filename, _) in zip(
                    next_f_indices, filename_and_terms
                )
            ),
            many=True,
        )
        unique_terms = set.union(*(set(couple[1]) for couple in filename_and_terms))
        term_to_id = {
            row["term"]: row["term_id"]
            for row in self.sql_database.query(
                f"SELECT term_id, term FROM term WHERE "
                f"term IN ({','.join('?' for _ in unique_terms)})",
                tuple(unique_terms),
            )
        }
        missing_terms = sorted(unique_terms - set(term_to_id))
        if missing_terms:
            last_tid = self.sql_database.query_one(
                "SELECT MAX(term_id) AS last_id FROM term"
            )["last_id"]
            next_term_indices = list(
                range(last_tid + 1, last_tid + 1 + len(missing_terms))
            )
            self.sql_database.modify(
                "INSERT INTO term (term_id, term) VALUES (?,?)",
                zip(next_term_indices, missing_terms),
                many=True,
            )
            term_to_id.update(
                {
                    term: term_id
                    for term, term_id in zip(missing_terms, next_term_indices)
                }
            )
        self.sql_database.modify(
            "INSERT INTO filename_to_term "
            "(filename_id, term_id, term_rank) VALUES (?,?,?)",
            (
                (filename_id, term_to_id[term], term_rank)
                for filename_id, (_, terms) in zip(next_f_indices, filename_and_terms)
                for term_rank, term in enumerate(terms)
            ),
            many=True,
        )

    def _add_video(self, video: Video):
        logger.info(f"Video indexing: {video.filename.path}")
        filename_id = self.sql_database.modify(
            "INSERT INTO filename (filename) VALUES (?)", [video.filename.path]
        )
        for term_rank, term in enumerate(video.terms()):
            term_id = self.sql_database.select_id_from_values(
                "term", "term_id", term=term
            ) or self.sql_database.insert("term", term=term)
            self.sql_database.insert(
                "filename_to_term",
                filename_id=filename_id,
                term_id=term_id,
                term_rank=term_rank,
            )

    def _remove_filename(self, filename: AbsolutePath) -> None:
        self.sql_database.modify(
            "DELETE FROM filename WHERE filename = ?", [filename.path]
        )

    def _term_to_filenames(self, term: str) -> Iterable[AbsolutePath]:
        return (
            AbsolutePath(row["filename"])
            for row in self.sql_database.query(
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
        # TODO Better, with one query? https://dba.stackexchange.com/a/45516
        terms = sorted(set(terms))
        pieces_filename_to_term = []
        pieces_terms = []
        pieces_where = []
        query = ["SELECT DISTINCT f.filename AS filename FROM filename AS f"]
        for i, term in enumerate(terms):
            pieces_filename_to_term.append(
                f"JOIN filename_to_term AS j{i} ON f.filename_id = j{i}.filename_id"
            )
            pieces_terms.append(f"JOIN term as t{i} ON j{i}.term_id = t{i}.term_id")
            pieces_where.append(f"t{i}.term = ?")
        query.extend(pieces_filename_to_term)
        query.extend(pieces_terms)
        query.append("WHERE")
        query.append(" AND ".join(pieces_where))
        return set(filenames) & {
            AbsolutePath(r["filename"])
            for r in self.sql_database.query(" ".join(query), terms, debug=True)
        }

    def query_or(
        self, filenames: Iterable[AbsolutePath], terms: Sequence[str]
    ) -> Iterable[AbsolutePath]:
        return set(filenames) & set.union(
            *(set(self._term_to_filenames(term)) for term in terms)
        )
