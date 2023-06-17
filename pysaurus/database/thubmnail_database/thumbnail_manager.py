import base64
from io import BytesIO
from typing import Optional

from pysaurus.core.components import AbsolutePath
from pysaurus.database.thubmnail_database.thumbnail_database import ThumbnailDatabase
from pysaurus.video_raptor.video_raptor_pyav import VideoRaptor


class ThumbnailManager:
    __slots__ = ("thumb_db", "raptor")

    def __init__(self, db_path: AbsolutePath):
        self.thumb_db = ThumbnailDatabase(db_path.path)
        self.raptor = VideoRaptor()

    def build(self, videos: dict):
        thumbnail_path_to_filenames = {}
        for video in videos:
            thumbnail_path_to_filenames.setdefault(video["thumbnail_path"], []).append(
                video["filename"]
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

    def has(self, filename: AbsolutePath) -> bool:
        return self.thumb_db.count(
            "video_to_thumbnail", "filename", "filename = ?", [filename.path]
        )

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

    def save(self, video_filename: AbsolutePath) -> Optional[dict]:
        blob = BytesIO()
        err = self.raptor.get_thumbnail(video_filename.path, blob)
        if not err:
            self.thumb_db.modify(
                "INSERT OR IGNORE INTO video_to_thumbnail "
                "(filename, thumbnail) VALUES (?, ?)",
                [video_filename.path, blob.getvalue()],
            )
        return err

    def rename(self, old_path: AbsolutePath, new_path: AbsolutePath):
        self.thumb_db.modify(
            "UPDATE video_to_thumbnail SET filename = ? WHERE filename = ?",
            (new_path.path, old_path.path),
        )

    def delete(self, path: AbsolutePath):
        self.thumb_db.modify(
            "DELETE FROM video_to_thumbnail WHERE filename = ?", [path.path]
        )
