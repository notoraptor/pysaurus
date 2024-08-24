PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS video_to_thumbnail (
    filename TEXT NOT NULL,
    thumbnail BLOB NOT NULL,
    UNIQUE (filename)
);
