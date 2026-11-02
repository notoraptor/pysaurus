"""``VideoRuntimeInfo.is_same_file``: equality, or exactly the drift a FAT-style
volume shows when the local UTC offset changed between two reads."""

from pysaurus.video.video_runtime_info import VideoRuntimeInfo

SUMMER = -14400  # EDT
WINTER = -18000  # EST
T = 1_752_580_800.0  # 2025-07-15 12:00 UTC


def _disk(mtime: float, offset: int | None = WINTER, size: int = 10):
    return VideoRuntimeInfo(
        size=size, mtime=mtime, mtime_utc_offset=offset, is_file=True
    )


def test_equal_reading_is_same_file():
    assert _disk(T).is_same_file(T, WINTER, 10)
    # A stable volume (NTFS) across a DST change: still equal, still the same file.
    assert _disk(T).is_same_file(T, SUMMER, 10)


def test_size_change_always_differs():
    assert not _disk(T, size=11).is_same_file(T, WINTER, 10)
    assert not _disk(T + 3600, size=11).is_same_file(T, SUMMER, 10)


def test_fat_drift_matches_the_offset_change():
    # Saved in summer (UTC-4), read in winter (UTC-5): FAT reports one hour later.
    assert _disk(T + 3600, WINTER).is_same_file(T, SUMMER, 10)
    assert _disk(T - 3600, SUMMER).is_same_file(T, WINTER, 10)


def test_drift_in_the_wrong_direction_is_a_change():
    assert not _disk(T - 3600, WINTER).is_same_file(T, SUMMER, 10)


def test_one_hour_without_offset_change_is_a_change():
    assert not _disk(T + 3600, WINTER).is_same_file(T, WINTER, 10)
    assert not _disk(T + 3600, SUMMER).is_same_file(T, SUMMER, 10)


def test_any_other_delta_is_a_change():
    assert not _disk(T + 1).is_same_file(T, WINTER, 10)
    assert not _disk(T + 7200, WINTER).is_same_file(T, SUMMER, 10)


def test_half_hour_zones_use_the_actual_offset_change():
    # Lord Howe Island: +10:30 standard, +11:00 daylight.
    assert _disk(T + 1800, 37800).is_same_file(T, 39600, 10)
    assert not _disk(T + 3600, 37800).is_same_file(T, 39600, 10)


def test_legacy_row_gets_one_hour_of_slack_either_way():
    assert _disk(T + 3600).is_same_file(T, None, 10)
    assert _disk(T - 3600).is_same_file(T, None, 10)
    assert not _disk(T + 1).is_same_file(T, None, 10)
    assert not _disk(T + 7200).is_same_file(T, None, 10)


def test_reading_without_offset_only_matches_equality():
    assert _disk(T, None).is_same_file(T, WINTER, 10)
    assert not _disk(T + 3600, None).is_same_file(T, SUMMER, 10)
