"""``date_added``: seeded at collection, untouched by rescans, inherited by
moves, and a field of its own next to the file date."""

import pytest

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection
from pysaurus.video.video_entry import VideoEntry
from pysaurus.video.video_runtime_info import VideoRuntimeInfo

TS_OLD = 1_546_300_800.0  # 2019-01-01 UTC
TS_NEW = 1_767_225_600.0  # 2026-01-01 UTC
FRESH = "C:\\fresh.mkv"


@pytest.fixture
def db(mem_saurus_database) -> PysaurusCollection:
    return mem_saurus_database


def _collect(db: PysaurusCollection, filename: str, mtime: float) -> int:
    """Run one file through videos_add, as a folder scan would."""
    path = AbsolutePath(filename)
    info = VideoRuntimeInfo(size=10, mtime=mtime, driver_id="C:\\", is_file=True)
    entry = VideoEntry(filename=path.path, duration=1.0, duration_time_base=1)
    db.videos_add([entry], {path: info})
    (video,) = db.get_videos(include=["video_id"], where={"filename": path})
    return video.video_id


def _video(db: PysaurusCollection, video_id: int):
    (video,) = db.get_videos(include=["date_added"], where={"video_id": video_id})
    return video


def _move_pair(db: PysaurusCollection) -> tuple[int, int]:
    """Two videos set up as a move: src not-found, dst found."""
    src, dst = [v.video_id for v in db.get_videos(include=["video_id"])][:2]
    db.videos_set_field("found", {src: False, dst: True})
    return src, dst


def test_collect_dates_a_new_video_from_its_file(db):
    video = _video(db, _collect(db, FRESH, TS_OLD))
    assert video.date_added == TS_OLD == video.mtime


def test_rescanning_a_changed_file_keeps_date_added(db):
    video_id = _collect(db, FRESH, TS_OLD)
    assert _collect(db, FRESH, TS_NEW) == video_id
    video = _video(db, video_id)
    assert video.mtime == TS_NEW
    assert video.date_added == TS_OLD


def test_date_added_is_its_own_field(db):
    video_id = _collect(db, FRESH, TS_NEW)
    db.videos_set_field("date_added", {video_id: TS_OLD})
    video = _video(db, video_id)
    assert video.date_added == TS_OLD
    assert video.date.time == TS_NEW
    (row,) = db.db.query_all(f"SELECT day, year FROM video WHERE video_id = {video_id}")
    assert (row["day"], row["year"]) == ("2026-01-01", "2026")


def test_move_keeps_the_earliest_date_added(db):
    src, dst = _move_pair(db)
    db.videos_set_field("date_added", {src: TS_OLD, dst: TS_NEW})
    db.algos.move_video_entries([(src, dst)])
    assert _video(db, dst).date_added == TS_OLD


def test_move_ignores_an_unknown_source_date(db):
    src, dst = _move_pair(db)
    db.videos_set_field("date_added", {src: 0.0, dst: TS_NEW})
    db.algos.move_video_entries([(src, dst)])
    assert _video(db, dst).date_added == TS_NEW
