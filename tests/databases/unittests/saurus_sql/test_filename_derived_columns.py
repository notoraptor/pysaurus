"""
Tests that the SQL STORED extension/file_title columns (database.sql) agree
exactly with AbsolutePath.extension / AbsolutePath.file_title, on the same
leading-dot edge cases the two implementations were reconciled on.

Uses mem_saurus_database (in-memory copy) so inserted rows never touch the
on-disk fixture.
"""

import pytest

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection

BASENAMES = [
    "video.mp4",
    "VIDEO.MP4",
    "archive.tar.gz",
    "noext",
    ".gitignore",
    ".env",
    "..backup",
    "...hidden",
    "....a",
    ".a.b",
    "..a...b",
    "...a.b....c.d",
    "file with spaces.mp4",
    "émoji_clip.mp4",
    "日本語.mp4",
]


@pytest.fixture
def db(mem_saurus_database) -> PysaurusCollection:
    return mem_saurus_database


@pytest.mark.parametrize("basename", BASENAMES)
def test_stored_columns_match_absolute_path(db, basename, tmp_path):
    # Stabilize exactly like the real scan pipeline: filename in the DB is
    # always AbsolutePath(...).standard_path. A second AbsolutePath() over
    # it must be a no-op, otherwise this basename could never be what's
    # really stored (e.g. a name made only of dots, or with trailing dots).
    candidate = AbsolutePath(str(tmp_path / basename))
    filename = candidate.standard_path
    assert AbsolutePath(filename).standard_path == filename, (
        f"{basename!r} does not round-trip through AbsolutePath: not a "
        "realistic stored filename"
    )

    db.db.modify("INSERT INTO video (filename) VALUES (?)", [filename])
    row = db.db.query_one(
        "SELECT extension, file_title FROM video WHERE filename = ?", [filename]
    )

    assert row["extension"] == candidate.extension
    assert row["file_title"] == candidate.file_title
