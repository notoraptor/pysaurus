from skullite import Skullite


SCRIPT = """
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS video_to_thumbnail (
    filename TEXT NOT NULL,
    thumbnail BLOB NOT NULL,
    UNIQUE (filename)
);
"""


class ThumbnailDatabase(Skullite):
    __slots__ = ()

    def __init__(self, db_path: str):
        super().__init__(db_path, script=SCRIPT)
