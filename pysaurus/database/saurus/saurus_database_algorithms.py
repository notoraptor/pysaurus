from typing import Container

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.database.database_algorithms import DatabaseAlgorithms
from pysaurus.video import VideoRuntimeInfo


class SaurusDatabaseAlgorithms(DatabaseAlgorithms):
    """SQL-optimized database algorithms."""

    def _update_videos_not_found(self, existing_paths: Container[AbsolutePath]):
        db = self.db.db
        db.modify("UPDATE video SET is_file = 0 WHERE is_file != 0")
        if existing_paths:
            db.modify_many(
                "UPDATE video SET is_file = 1 WHERE filename = ?",
                ((p.path,) for p in existing_paths),
            )

    def _find_video_paths_for_update(
        self, file_paths: dict[AbsolutePath, VideoRuntimeInfo]
    ) -> list[AbsolutePath]:
        db = self.db.db
        # Load all (filename, mtime, file_size, driver_id) from DB in one query.
        # driver_id is TEXT in SQL but int in VideoRuntimeInfo, so cast back.
        with db:
            existing = {
                row[0]: (row[1], row[2], int(row[3]) if row[3] is not None else None)
                for row in db.query(
                    "SELECT filename, mtime, file_size, driver_id FROM video"
                )
            }
        # Compare in memory: file needs update if not in DB or any field changed
        return sorted(
            file_name
            for file_name, file_info in file_paths.items()
            if existing.get(file_name.path)
            != (file_info.mtime, file_info.size, file_info.driver_id)
        )
