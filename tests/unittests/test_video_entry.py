"""``VideoEntry.to_table``: ``date_added`` is written once, at insertion."""

from pysaurus.video.video_entry import VideoEntry
from pysaurus.video.video_runtime_info import VideoRuntimeInfo


def _runtime(mtime: float) -> VideoRuntimeInfo:
    return VideoRuntimeInfo(size=10, mtime=mtime, driver_id="C:\\", is_file=True)


def test_new_entry_is_dated_from_its_file():
    row = VideoEntry(filename="C:\\a.mkv").to_table(False, _runtime(1000.0))
    assert row["mtime"] == 1000.0
    assert row["date_added"] == 1000.0
    assert "video_id" not in row


def test_explicit_date_added_wins_over_mtime():
    entry = VideoEntry(filename="C:\\a.mkv", date_added=5.0)
    assert entry.to_table(False, _runtime(1000.0))["date_added"] == 5.0


def test_update_never_touches_date_added():
    row = VideoEntry(filename="C:\\a.mkv", video_id=3).to_table(True, _runtime(2000.0))
    assert "date_added" not in row
    assert row["mtime"] == 2000.0
    assert row["video_id"] == 3
