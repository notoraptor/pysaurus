from typing import TYPE_CHECKING, Collection, Container, cast

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.database.database_algorithms import DatabaseAlgorithms
from pysaurus.video.video_runtime_info import VideoRuntimeInfo

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

    def _find_video_paths_for_update(
        self, file_paths: dict[AbsolutePath, VideoRuntimeInfo]
    ) -> list[AbsolutePath]:
        db = cast("PysaurusCollection", self.db).db
        # Load all (filename, mtime, file_size) from DB in one query.
        with db:
            existing = {
                row[0]: (row[1], row[2])
                for row in db.query("SELECT filename, mtime, file_size FROM video")
            }
        # Compare in memory: file needs update if not in DB or any field changed
        return sorted(
            file_name
            for file_name, file_info in file_paths.items()
            if existing.get(file_name.path) != (file_info.mtime, file_info.size)
        )
