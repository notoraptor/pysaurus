"""`discarded` is derived, so it is recomputed rather than trusted.

It says whether a video sits outside the source folders. Nothing the user does
sets it directly, and it can drift -- a database built while paths and sources
disagreed on the case of their drive carries rows wrongly marked discarded,
which makes them invisible everywhere (`WHERE v.discarded = 0`). Recomputing it
during update() is what repairs those, since changing the folder list is the
only other trigger and normalized paths make that comparison always equal.
"""

import pytest

from pysaurus.application.application import Application
from pysaurus.core.absolute_path import AbsolutePath


@pytest.fixture
def db(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    videos = tmp_path / "Videos"
    videos.mkdir()
    app = Application(home_dir=str(home))
    database = app.new_database("mydb", [])
    database.ops.set_folders([AbsolutePath(str(videos))])
    for name in ("a.mkv", "b.mkv"):
        database.db.modify(
            "INSERT INTO video (filename) VALUES (?)", [str(videos / name)]
        )
    return database


def _discarded(database) -> list[int]:
    return [
        row["discarded"]
        for row in database.db.query_all(
            "SELECT discarded FROM video ORDER BY filename"
        )
    ]


def test_a_stale_flag_is_repaired(db):
    """The inherited case: rows wrongly marked, with no folder change to make."""
    db.db.modify("UPDATE video SET discarded = 1")
    assert _discarded(db) == [1, 1]
    db.refresh_discarded()
    assert _discarded(db) == [0, 0]


def test_a_video_outside_the_folders_is_discarded(db, tmp_path):
    outside = tmp_path / "Elsewhere"
    outside.mkdir()
    db.db.modify("INSERT INTO video (filename) VALUES (?)", [str(outside / "c.mkv")])
    db.refresh_discarded()
    # Ordered by filename: Elsewhere/c.mkv first, then the two under Videos.
    assert _discarded(db) == [1, 0, 0]


def test_explicit_folders_win_over_the_stored_ones(db, tmp_path):
    """_set_folders computes the flag for the list it is about to store."""
    db.refresh_discarded([AbsolutePath(str(tmp_path / "Elsewhere"))])
    assert _discarded(db) == [1, 1]


def test_update_recomputes_it(db, monkeypatch):
    """The whole point: an update repairs the flag without any user action.

    The source folder is empty, so the scan finds nothing and only the existing
    rows are revisited -- which is exactly the path that used to leave them
    marked.
    """
    db.db.modify("UPDATE video SET discarded = 1")
    calls = []
    original = type(db).refresh_discarded
    monkeypatch.setattr(
        type(db),
        "refresh_discarded",
        lambda self, folders=None: (calls.append(1), original(self, folders))[1],
    )
    db.algos.update()
    assert calls, "update() must recompute discarded"
    assert _discarded(db) == [0, 0]
