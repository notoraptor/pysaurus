import base64
from typing import Dict, Iterable, List, Set

from pysaurus.core.components import AbsolutePath
from pysaurus.database.jsdb.thubmnail_database.thumbnail_database import (
    ThumbnailDatabase,
)
from pysaurus.video.video_pattern import VideoPattern
from pysaurus.video_raptor.video_raptor_pyav import PythonVideoRaptor


class ThumbnailManager:
    __slots__ = ("thumb_db", "raptor")

    def __init__(self, db_path: AbsolutePath):
        self.thumb_db = ThumbnailDatabase(db_path.path)
        self.raptor = PythonVideoRaptor()

    def build(self, videos: Iterable[VideoPattern]):
        thumbnail_path_to_filenames = {}
        for video in videos:
            thumbnail_path_to_filenames.setdefault(video.thumbnail_path, []).append(
                video.filename
            )
        filename_and_thumbnail_path = [
            (filenames[0], thumb)
            for thumb, filenames in thumbnail_path_to_filenames.items()
            if len(filenames) == 1 and thumb.isfile()
        ]
        self.thumb_db.modify(
            "INSERT INTO video_to_thumbnail (filename, thumbnail) VALUES (?, ?)",
            (
                (filename.path, thumb_path.read_binary_file())
                for filename, thumb_path in filename_and_thumbnail_path
            ),
            many=True,
        )

    def save_existing_thumbnails(self, filename_to_thumb_name: Dict[str, str]):
        self.thumb_db.modify(
            "INSERT OR IGNORE INTO video_to_thumbnail "
            "(filename, thumbnail) VALUES (?, ?)",
            [
                (filename, AbsolutePath(thumb_path).read_binary_file())
                for filename, thumb_path in filename_to_thumb_name.items()
            ],
            many=True,
        )

    def has(self, filename: AbsolutePath) -> bool:
        return self.thumb_db.count(
            "video_to_thumbnail", "filename", "filename = ?", [filename.path]
        )

    def filter(self, filenames: Iterable[str]) -> Set[str]:
        if not isinstance(filenames, (list, tuple, set)):
            filenames = list(filenames)
        return {
            row["filename"]
            for row in self.thumb_db.query(
                f"SELECT filename FROM video_to_thumbnail "
                f"WHERE filename in ({','.join(['?'] * len(filenames))})",
                filenames,
            )
        }

    def get_blob(self, filename: AbsolutePath, wrapper=None):
        rows = self.thumb_db.query_all(
            "SELECT thumbnail FROM video_to_thumbnail WHERE filename = ?",
            [filename.path],
        )
        if rows:
            (row,) = rows
            return wrapper(row["thumbnail"]) if wrapper else row["thumbnail"]
        return None

    def get_base64(self, filename: AbsolutePath):
        return self.get_blob(filename, wrapper=base64.b64encode)

    def rename(self, old_path: AbsolutePath, new_path: AbsolutePath):
        self.thumb_db.modify(
            "UPDATE video_to_thumbnail SET filename = ? WHERE filename = ?",
            (new_path.path, old_path.path),
        )

    def delete(self, path: AbsolutePath):
        self.thumb_db.modify(
            "DELETE FROM video_to_thumbnail WHERE filename = ?", [path.path]
        )

    def clean_thumbnails(self, paths: List[AbsolutePath]):
        paths = set(paths)
        absent = [
            row
            for row in self.thumb_db.query("SELECT filename FROM video_to_thumbnail")
            if AbsolutePath(row["filename"]) not in paths
        ]
        self.thumb_db.modify(
            "DELETE FROM video_to_thumbnail WHERE filename = ?", absent, many=True
        )
