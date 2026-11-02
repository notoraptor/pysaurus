import time

import pytest

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.database.database_algorithms import DatabaseAlgorithms
from pysaurus.database.saurus.saurus_database_algorithms import SaurusDatabaseAlgorithms
from pysaurus.video.video_runtime_info import VideoRuntimeInfo


def _get_all_found(db) -> dict[str, bool]:
    """Return {filename: found} for all videos."""
    return {
        v.filename.path: v.found for v in db.get_videos(include=["filename", "found"])
    }


def _get_runtime_info(db) -> dict[AbsolutePath, VideoRuntimeInfo]:
    """Build a runtime info dict from all videos in db (simulates disk scan)."""
    result = {}
    for v in db.get_videos(
        include=["filename", "file_size", "mtime", "mtime_utc_offset", "driver_id"],
        where={"found": True},
    ):
        result[v.filename] = VideoRuntimeInfo(
            size=v.file_size,
            mtime=v.mtime,
            mtime_utc_offset=v.mtime_utc_offset,
            driver_id=v.driver_id,
            is_file=True,
        )
    return result


SUMMER = -14400  # EDT
WINTER = -18000  # EST


def _save_stamp(db, path: AbsolutePath, mtime: float, offset: int | None) -> None:
    db.db.modify(
        "UPDATE video SET mtime = ?, mtime_utc_offset = ? WHERE filename = ?",
        [mtime, offset, path.path],
    )


def _saved_stamp(db, path: AbsolutePath) -> tuple:
    return tuple(
        db.db.query_one(
            "SELECT mtime, mtime_utc_offset FROM video WHERE filename = ?", [path.path]
        )
    )


# =========================================================================
# Unit tests
# =========================================================================


class TestUpdateVideosNotFound:
    def test_marks_missing_videos_as_not_found(self, mem_saurus_database):
        db = mem_saurus_database
        all_videos = db.get_videos(include=["filename"])
        # Keep only half the videos as "existing on disk"
        half = len(all_videos) // 2
        existing = {v.filename for v in all_videos[:half]}
        missing = {v.filename.path for v in all_videos[half:]}

        db.algos._update_videos_not_found(existing)

        found_map = _get_all_found(db)
        for path in missing:
            assert not found_map[path], f"{path} should be not found"
        for p in existing:
            assert found_map[p.path], f"{p} should be found"

    def test_empty_paths_marks_all_not_found(self, mem_saurus_database):
        db = mem_saurus_database
        db.algos._update_videos_not_found({})

        found_map = _get_all_found(db)
        assert all(not found for found in found_map.values())

    def test_all_paths_marks_all_found(self, mem_saurus_database):
        db = mem_saurus_database
        all_paths = {v.filename for v in db.get_videos(include=["filename"])}

        db.algos._update_videos_not_found(all_paths)

        found_map = _get_all_found(db)
        assert all(found for found in found_map.values())

    def test_same_result_as_base_class(self, mem_saurus_database):
        """SQL-optimized version produces same results as base class."""
        db = mem_saurus_database
        all_videos = db.get_videos(include=["filename"])
        existing = {v.filename for v in all_videos[: len(all_videos) // 3]}

        # Run base class version
        DatabaseAlgorithms(db)._update_videos_not_found(existing)
        base_result = _get_all_found(db)

        # Reset all to found
        db.db.modify("UPDATE video SET is_file = 1")

        # Run SQL-optimized version
        SaurusDatabaseAlgorithms(db)._update_videos_not_found(existing)
        sql_result = _get_all_found(db)

        assert base_result == sql_result


class TestFindVideoPathsForUpdate:
    def test_unchanged_files_not_returned(self, mem_saurus_database):
        db = mem_saurus_database
        file_paths = _get_runtime_info(db)

        result = db.algos._find_video_paths_for_update(file_paths)
        assert result == []

    def test_new_file_returned(self, mem_saurus_database):
        db = mem_saurus_database
        file_paths = _get_runtime_info(db)
        new_path = AbsolutePath("/videos/brand_new_video.mp4")
        file_paths[new_path] = VideoRuntimeInfo(
            size=999, mtime=99999.0, driver_id="/videos", is_file=True
        )

        result = db.algos._find_video_paths_for_update(file_paths)
        assert new_path in result

    def test_modified_mtime_returned(self, mem_saurus_database):
        db = mem_saurus_database
        file_paths = _get_runtime_info(db)
        # Pick one file and change its mtime
        target = next(iter(file_paths))
        info = file_paths[target]
        file_paths[target] = VideoRuntimeInfo(
            size=info.size,
            mtime=info.mtime + 1.0,
            driver_id=info.driver_id,
            is_file=True,
        )

        result = db.algos._find_video_paths_for_update(file_paths)
        assert target in result

    def test_modified_size_returned(self, mem_saurus_database):
        db = mem_saurus_database
        file_paths = _get_runtime_info(db)
        target = next(iter(file_paths))
        info = file_paths[target]
        file_paths[target] = VideoRuntimeInfo(
            size=info.size + 1, mtime=info.mtime, driver_id=info.driver_id, is_file=True
        )

        result = db.algos._find_video_paths_for_update(file_paths)
        assert target in result

    def test_changed_driver_id_not_returned(self, mem_saurus_database):
        """Changing driver_id alone should not trigger a re-extraction."""
        db = mem_saurus_database
        file_paths = _get_runtime_info(db)
        # Change driver_id for all files
        for path, info in file_paths.items():
            file_paths[path] = VideoRuntimeInfo(
                size=info.size,
                mtime=info.mtime,
                driver_id="/different/mount",
                is_file=True,
            )

        result = db.algos._find_video_paths_for_update(file_paths)
        assert result == []

    def test_same_result_as_base_class(self, mem_saurus_database):
        """SQL-optimized version produces same results as base class."""
        db = mem_saurus_database
        file_paths = _get_runtime_info(db)
        # Modify a few files
        modified = []
        for i, (path, info) in enumerate(file_paths.items()):
            if i % 100 == 0:
                file_paths[path] = VideoRuntimeInfo(
                    size=info.size + 1,
                    mtime=info.mtime,
                    driver_id=info.driver_id,
                    is_file=True,
                )
                modified.append(path)
        # Add a new file
        new_path = AbsolutePath("/videos/new_video.mp4")
        file_paths[new_path] = VideoRuntimeInfo(
            size=1000, mtime=1.0, driver_id="/videos", is_file=True
        )

        base_result = DatabaseAlgorithms(db)._find_video_paths_for_update(file_paths)
        sql_result = SaurusDatabaseAlgorithms(db)._find_video_paths_for_update(
            file_paths
        )

        assert base_result == sql_result


class TestMtimeDrift:
    """A FAT-style volume reports an untouched file one hour off after a DST
    change; the row's recorded offset tells that drift from a real change."""

    @pytest.fixture(params=[DatabaseAlgorithms, SaurusDatabaseAlgorithms])
    def algos(self, request, mem_saurus_database):
        return request.param(mem_saurus_database)

    @staticmethod
    def _one_file(algos, saved_mtime, saved_offset, disk_mtime, disk_offset=WINTER):
        file_paths = _get_runtime_info(algos.db)
        target, info = next(iter(file_paths.items()))
        _save_stamp(algos.db, target, saved_mtime, saved_offset)
        file_paths[target] = VideoRuntimeInfo(
            size=info.size,
            mtime=disk_mtime,
            mtime_utc_offset=disk_offset,
            driver_id=info.driver_id,
            is_file=True,
        )
        return target, file_paths

    def test_drift_matching_the_offset_change_is_not_an_update(self, algos):
        target, file_paths = self._one_file(algos, 1000.0, SUMMER, 4600.0)
        assert target not in algos._find_video_paths_for_update(file_paths)
        assert _saved_stamp(algos.db, target) == (1000.0, SUMMER)

    def test_one_hour_without_offset_change_is_an_update(self, algos):
        target, file_paths = self._one_file(algos, 1000.0, WINTER, 4600.0)
        assert target in algos._find_video_paths_for_update(file_paths)

    def test_stable_file_across_offset_change_is_not_an_update(self, algos):
        target, file_paths = self._one_file(algos, 1000.0, SUMMER, 1000.0)
        assert target not in algos._find_video_paths_for_update(file_paths)

    def test_legacy_row_is_matched_with_slack_then_stamped(self, algos):
        target, file_paths = self._one_file(algos, 1000.0, None, 4600.0)
        assert target not in algos._find_video_paths_for_update(file_paths)
        assert _saved_stamp(algos.db, target) == (4600.0, WINTER)

    def test_legacy_row_equal_reading_is_stamped(self, algos):
        target, file_paths = self._one_file(algos, 1000.0, None, 1000.0)
        assert target not in algos._find_video_paths_for_update(file_paths)
        assert _saved_stamp(algos.db, target) == (1000.0, WINTER)

    def test_legacy_row_beyond_slack_is_an_update_and_kept(self, algos):
        target, file_paths = self._one_file(algos, 1000.0, None, 1001.0)
        assert target in algos._find_video_paths_for_update(file_paths)
        assert _saved_stamp(algos.db, target) == (1000.0, None)


# =========================================================================
# Benchmarks (run with pytest -s to see output)
# =========================================================================


class TestBenchmarks:
    @pytest.fixture
    def bench_db(self, mem_saurus_database):
        return mem_saurus_database

    def test_benchmark_update_videos_not_found(self, bench_db):
        db = bench_db
        all_videos = db.get_videos(include=["filename"])
        existing = {v.filename for v in all_videos[: len(all_videos) // 2]}
        n_runs = 5

        # Benchmark base class
        base_times = []
        for _ in range(n_runs):
            db.db.modify("UPDATE video SET is_file = 1")
            t0 = time.perf_counter()
            DatabaseAlgorithms(db)._update_videos_not_found(existing)
            base_times.append(time.perf_counter() - t0)

        # Benchmark SQL-optimized
        sql_times = []
        for _ in range(n_runs):
            db.db.modify("UPDATE video SET is_file = 1")
            t0 = time.perf_counter()
            SaurusDatabaseAlgorithms(db)._update_videos_not_found(existing)
            sql_times.append(time.perf_counter() - t0)

        base_avg = sum(base_times) / n_runs
        sql_avg = sum(sql_times) / n_runs
        speedup = base_avg / sql_avg if sql_avg else float("inf")
        nb = len(all_videos)
        print(
            f"\n_update_videos_not_found ({nb} videos, {len(existing)} existing):"
            f"\n  Base:  {base_avg:.4f}s"
            f"\n  SQL:   {sql_avg:.4f}s"
            f"\n  Speedup: {speedup:.1f}x"
        )

    def test_benchmark_find_video_paths_for_update(self, bench_db):
        db = bench_db
        file_paths = _get_runtime_info(db)
        # Modify 1% of files
        for i, (path, info) in enumerate(file_paths.items()):
            if i % 100 == 0:
                file_paths[path] = VideoRuntimeInfo(
                    size=info.size + 1,
                    mtime=info.mtime,
                    driver_id=info.driver_id,
                    is_file=True,
                )
        n_runs = 3

        # Benchmark base class
        base_times = []
        for _ in range(n_runs):
            t0 = time.perf_counter()
            DatabaseAlgorithms(db)._find_video_paths_for_update(file_paths)
            base_times.append(time.perf_counter() - t0)

        # Benchmark SQL-optimized
        sql_times = []
        for _ in range(n_runs):
            t0 = time.perf_counter()
            SaurusDatabaseAlgorithms(db)._find_video_paths_for_update(file_paths)
            sql_times.append(time.perf_counter() - t0)

        base_avg = sum(base_times) / n_runs
        sql_avg = sum(sql_times) / n_runs
        speedup = base_avg / sql_avg if sql_avg else float("inf")
        nb = len(file_paths)
        print(
            f"\n_find_video_paths_for_update ({nb} files, 1% modified):"
            f"\n  Base:  {base_avg:.4f}s"
            f"\n  SQL:   {sql_avg:.4f}s"
            f"\n  Speedup: {speedup:.1f}x"
        )
