"""Tests for the per-disk interleaving of collect tasks (Videos.hunt).

Paths reach hunt() sorted, hence grouped by disk: without interleaving the
workers saturate one disk at a time while the others sit idle.
"""

import os

import pytest

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.database.algorithms.videos import Videos
from pysaurus.video.video_runtime_info import VideoRuntimeInfo
from pysaurus.video_raptor.video_raptor_pyav import VideoTask


def make_task(path: str) -> VideoTask:
    return VideoTask(AbsolutePath(path), need_info=True)


def runtime(tasks_and_mounts) -> dict[AbsolutePath, VideoRuntimeInfo]:
    return {
        task.filename: VideoRuntimeInfo(driver_id=mount)
        for task, mount in tasks_and_mounts
    }


def test_interleaves_between_mount_points():
    a = [make_task(f"/disk_a/{i}.mp4") for i in range(3)]
    b = [make_task(f"/disk_b/{i}.mp4") for i in range(3)]
    tasks = a + b  # sorted order: one disk fully, then the other
    info = runtime([(t, "A") for t in a] + [(t, "B") for t in b])

    result = Videos._interleave_by_disk(tasks, info)

    assert result == [a[0], b[0], a[1], b[1], a[2], b[2]]


def test_uneven_groups_keep_every_task():
    a = [make_task(f"/disk_a/{i}.mp4") for i in range(5)]
    b = [make_task(f"/disk_b/{i}.mp4") for i in range(2)]
    tasks = a + b
    info = runtime([(t, "A") for t in a] + [(t, "B") for t in b])

    result = Videos._interleave_by_disk(tasks, info)

    assert len(result) == len(tasks)
    assert set(result) == set(tasks)
    # The short group is spread over the head, never truncated.
    assert result[:4] == [a[0], b[0], a[1], b[1]]


def test_single_mount_point_is_left_untouched():
    tasks = [make_task(f"/disk_a/{i}.mp4") for i in range(4)]
    info = runtime([(t, "A") for t in tasks])

    assert Videos._interleave_by_disk(tasks, info) is tasks


def test_missing_runtime_info_falls_back_on_the_drive():
    """A task absent from runtime_info still lands in a sensible group."""
    tasks = [make_task(f"/disk_a/{i}.mp4") for i in range(3)]

    result = Videos._interleave_by_disk(tasks, None)

    assert len(result) == len(tasks)
    assert set(result) == set(tasks)


@pytest.mark.skipif(os.name != "nt", reason="drive letters are Windows-only")
def test_drive_letters_group_without_runtime_info():
    c = [make_task(f"C:\\videos\\{i}.mp4") for i in range(2)]
    d = [make_task(f"D:\\videos\\{i}.mp4") for i in range(2)]

    result = Videos._interleave_by_disk(c + d, None)

    assert result == [c[0], d[0], c[1], d[1]]
