"""display_width/display_height, in SQL and in Python.

Storage dimensions are not what a player shows: non-square pixels stretch the
picture, and a display matrix turns it on its side. The generated columns exist
so the query engine can sort and filter on the displayed size; VideoPattern
recomputes the same values for the interface. Both must agree exactly, half a
pixel included, which is why both round with integer arithmetic.
"""

import pytest

# (width, height, rotation, sar_num, sar_den, display_width, display_height)
CASES = [
    (1920, 1080, 0, 1, 1, 1920, 1080),  # nothing to correct
    (1920, 1080, 90, 1, 1, 1080, 1920),  # portrait phone video
    (1920, 1080, 270, 1, 1, 1080, 1920),
    (1920, 1080, 180, 1, 1, 1920, 1080),  # upside down, same size
    (720, 576, 0, 64, 45, 1024, 576),  # PAL DVD, 16/9
    (720, 480, 0, 8, 9, 640, 480),  # NTSC DVD, 4/3
    (720, 576, 90, 64, 45, 576, 1024),  # both at once
    (101, 50, 0, 1, 2, 51, 50),  # exact half pixel, rounded up
    (640, 480, 0, 0, 0, 640, 480),  # degenerate ratio falls back to storage
]


@pytest.fixture
def db(mem_saurus_database):
    return mem_saurus_database.db


def _insert(db, index, width, height, rotation, sar_num, sar_den) -> int:
    db.modify(
        "INSERT INTO video (filename, width, height, rotation,"
        " sample_aspect_ratio_num, sample_aspect_ratio_den)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        [f"/geometry/{index}.mp4", width, height, rotation, sar_num, sar_den],
    )
    return db.query_one("SELECT MAX(video_id) AS id FROM video")["id"]


@pytest.mark.parametrize("case", CASES)
def test_generated_columns_give_the_displayed_size(db, case):
    width, height, rotation, num, den, expected_width, expected_height = case
    video_id = _insert(db, 0, width, height, rotation, num, den)
    row = db.query_one(
        "SELECT display_width, display_height FROM video WHERE video_id = ?", [video_id]
    )
    assert (row["display_width"], row["display_height"]) == (
        expected_width,
        expected_height,
    )


@pytest.mark.parametrize("case", CASES)
def test_python_matches_the_generated_columns(mem_saurus_database, case):
    width, height, rotation, num, den, expected_width, expected_height = case
    video_id = _insert(mem_saurus_database.db, 1, width, height, rotation, num, den)
    (video,) = mem_saurus_database.get_videos(
        include=None, where={"video_id": [video_id]}
    )
    assert (video.display_width, video.display_height) == (
        expected_width,
        expected_height,
    )


def test_has_display_geometry_flags_only_what_differs(mem_saurus_database):
    """A half-turn keeps the size but still counts; a degenerate ratio does not."""
    plain = _insert(mem_saurus_database.db, 2, 1920, 1080, 0, 1, 1)
    anamorphic = _insert(mem_saurus_database.db, 3, 720, 576, 0, 64, 45)
    rotated = _insert(mem_saurus_database.db, 4, 1920, 1080, 90, 1, 1)
    upside_down = _insert(mem_saurus_database.db, 5, 1920, 1080, 180, 1, 1)
    degenerate = _insert(mem_saurus_database.db, 6, 1920, 1080, 0, 0, 1)
    flags = {}
    for video_id in (plain, anamorphic, rotated, upside_down, degenerate):
        (video,) = mem_saurus_database.get_videos(
            include=None, where={"video_id": [video_id]}
        )
        flags[video_id] = video.has_display_geometry
    assert flags == {
        plain: False,
        anamorphic: True,
        rotated: True,
        upside_down: True,
        degenerate: False,
    }
