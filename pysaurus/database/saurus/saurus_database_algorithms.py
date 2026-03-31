from typing import cast, Collection

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.database.database_algorithms import DatabaseAlgorithms
from pysaurus.video.video_runtime_info import VideoRuntimeInfo


class SaurusDatabaseAlgorithms(DatabaseAlgorithms):
    """SQL-optimized database algorithms."""

    def _update_videos_not_found(self, existing_paths: Collection[AbsolutePath]):
        from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection

        db = cast(PysaurusCollection, self.db).db
        db.modify("UPDATE video SET is_file = 0 WHERE is_file != 0")
        if existing_paths:
            db.modify_many(
                "UPDATE video SET is_file = 1 WHERE filename = ?",
                ((p.path,) for p in existing_paths),
            )

    def _find_video_paths_for_update(
        self, file_paths: dict[AbsolutePath, VideoRuntimeInfo]
    ) -> list[AbsolutePath]:
        from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection

        db = cast(PysaurusCollection, self.db).db
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
