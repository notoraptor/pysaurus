from typing import TYPE_CHECKING, Collection, Container, cast

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.database.database_algorithms import DatabaseAlgorithms, FileStamp

if TYPE_CHECKING:
    from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection


class SaurusDatabaseAlgorithms(DatabaseAlgorithms):
    """SQL-optimized database algorithms."""

    def _update_videos_not_found(self, existing_paths: Collection[AbsolutePath]):
        db = cast("PysaurusCollection", self.db).db
        db.modify("UPDATE video SET is_file = 0 WHERE is_file != 0")
        if existing_paths:
            db.modify_many(
                "UPDATE video SET is_file = 1 WHERE filename = ?",
                ((p.path,) for p in existing_paths),
            )

    def _thumbnails_to_convert(
        self, done: Container[AbsolutePath]
    ) -> list[tuple[AbsolutePath, bytes]]:
        """Same set, streamed: an already known thumbnail is dropped on arrival.

        The base version materializes every thumbnail before filtering, which
        on a warm cache is hundreds of megabytes read for nothing.
        """
        db = cast("PysaurusCollection", self.db).db
        with db:
            return [
                (path, row[1])
                for row in db.query(
                    "SELECT v.filename, t.thumbnail FROM video AS v "
                    "JOIN video_thumbnail AS t ON v.video_id = t.video_id "
                    "WHERE v.unreadable = 0 AND LENGTH(t.thumbnail) > 0"
                )
                if (path := AbsolutePath(row[0])) not in done
            ]

    def _load_file_stamps(self) -> dict[str, FileStamp]:
        db = cast("PysaurusCollection", self.db).db
        with db:
            return {
                row[0]: FileStamp(row[1], row[2], row[3], row[4])
                for row in db.query(
                    "SELECT filename, video_id, mtime, mtime_utc_offset, file_size "
                    "FROM video"
                )
            }

    def _stamp_mtimes(self, stamps: dict[int, tuple[float, int]]) -> None:
        db = cast("PysaurusCollection", self.db).db
        db.modify_many(
            "UPDATE video SET mtime = ?, mtime_utc_offset = ? WHERE video_id = ?",
            ((mtime, offset, video_id) for video_id, (mtime, offset) in stamps.items()),
        )
