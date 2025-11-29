"""
Benchmark comparing JSON database vs Saurus SQL database performance.

This benchmark tests both read and write operations on 10,000 videos.
Both databases operate on disk (not in memory) for realistic conditions.

Run with: python tests/databases/scripts/benchmark_json_vs_saurus.py
"""

import gc
import os
import shutil
import statistics
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass, field

# Add project root to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
)


def _ignore_sqlite_wal_files(directory, files):
    """Ignore SQLite WAL files that may appear/disappear during copy."""
    return [f for f in files if f.endswith(("-wal", "-shm"))]


@dataclass
class BenchmarkResult:
    """Result of a single benchmark."""

    name: str
    json_times: list[float] = field(default_factory=list)
    saurus_times: list[float] = field(default_factory=list)

    @property
    def json_mean(self) -> float:
        return statistics.mean(self.json_times) if self.json_times else 0

    @property
    def saurus_mean(self) -> float:
        return statistics.mean(self.saurus_times) if self.saurus_times else 0

    @property
    def speedup(self) -> float:
        if self.saurus_mean == 0:
            return 0
        return self.json_mean / self.saurus_mean

    def __str__(self) -> str:
        json_ms = self.json_mean * 1000
        saurus_ms = self.saurus_mean * 1000
        if self.speedup >= 1:
            speedup_str = f"Saurus {self.speedup:.2f}x faster"
        else:
            speedup_str = f"JSON {1 / self.speedup:.2f}x faster"
        return f"{self.name:45} | JSON: {json_ms:10.2f}ms | Saurus: {saurus_ms:10.2f}ms | {speedup_str}"


@contextmanager
def timer():
    """Context manager to measure execution time."""
    gc.collect()
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    timer.elapsed = elapsed


def run_benchmark(
    name: str, json_db, saurus_db, json_fn, saurus_fn, iterations: int = 5
) -> BenchmarkResult:
    """Run a benchmark comparing JSON and Saurus SQL database.

    Args:
        json_db: JSON database instance (reused across iterations)
        saurus_db: Saurus SQL database instance (reused across iterations)
        json_fn: Function to benchmark on JSON database
        saurus_fn: Function to benchmark on Saurus SQL database
        iterations: Number of iterations to run
    """
    result = BenchmarkResult(name)

    for _ in range(iterations):
        # Benchmark JSON
        with timer():
            json_fn(json_db)
        result.json_times.append(timer.elapsed)

        # Benchmark Saurus SQL
        with timer():
            saurus_fn(saurus_db)
        result.saurus_times.append(timer.elapsed)

    return result


def run_read_benchmarks(json_db, saurus_db, all_video_ids, sample_100, sample_1000):
    """Run read-only benchmarks."""
    results = []

    # ==========================================================================
    # Basic read operations
    # ==========================================================================
    print("  Read operations...")

    # count_videos
    results.append(
        run_benchmark(
            "count_videos()",
            json_db,
            saurus_db,
            lambda db: db.count_videos(),
            lambda db: db.count_videos(),
        )
    )

    # get_videos() - all
    results.append(
        run_benchmark(
            "get_videos() - all 10k",
            json_db,
            saurus_db,
            lambda db: list(db.get_videos()),
            lambda db: list(db.get_videos()),
            iterations=3,
        )
    )

    # get_videos() - by video_id (single)
    results.append(
        run_benchmark(
            "get_videos(video_id=X) - single",
            json_db,
            saurus_db,
            lambda db: db.get_videos(where={"video_id": 500}),
            lambda db: db.get_videos(where={"video_id": 500}),
        )
    )

    # get_videos() - by video_id (100)
    results.append(
        run_benchmark(
            "get_videos(video_id=[...]) - 100 ids",
            json_db,
            saurus_db,
            lambda db: db.get_videos(where={"video_id": sample_100}),
            lambda db: db.get_videos(where={"video_id": sample_100}),
        )
    )

    # get_videos() - with filter readable=True
    results.append(
        run_benchmark(
            "get_videos(readable=True)",
            json_db,
            saurus_db,
            lambda db: list(db.get_videos(where={"readable": True})),
            lambda db: list(db.get_videos(where={"readable": True})),
            iterations=3,
        )
    )

    # ==========================================================================
    # Provider operations
    # ==========================================================================
    print("  Provider operations...")

    # Provider get_view_indices (default)
    results.append(
        run_benchmark(
            "provider.get_view_indices() - default",
            json_db,
            saurus_db,
            lambda db: db.provider.get_view_indices(),
            lambda db: db.provider.get_view_indices(),
        )
    )

    # Provider with search
    def json_search(db):
        db.provider.set_search("test", "and")
        return db.provider.get_view_indices()

    def saurus_search(db):
        db.provider.set_search("test", "and")
        return db.provider.get_view_indices()

    results.append(
        run_benchmark(
            "provider.set_search('test', 'and')",
            json_db,
            saurus_db,
            json_search,
            saurus_search,
        )
    )

    # Provider with grouping
    def json_group(db):
        db.provider.set_groups("extension")
        return db.provider.get_view_indices()

    def saurus_group(db):
        db.provider.set_groups("extension")
        return db.provider.get_view_indices()

    results.append(
        run_benchmark(
            "provider.set_groups('extension')",
            json_db,
            saurus_db,
            json_group,
            saurus_group,
        )
    )

    # Provider with sorting
    def json_sort(db):
        db.provider.set_sort(["-file_size"])
        return db.provider.get_view_indices()

    def saurus_sort(db):
        db.provider.set_sort(["-file_size"])
        return db.provider.get_view_indices()

    results.append(
        run_benchmark(
            "provider.set_sort(['-file_size'])",
            json_db,
            saurus_db,
            json_sort,
            saurus_sort,
        )
    )

    # Reset JSON provider only (Saurus creates fresh instances each time)
    json_db.provider.reset()

    # ==========================================================================
    # Property operations
    # ==========================================================================
    print("  Property operations...")

    # get_prop_types
    results.append(
        run_benchmark(
            "get_prop_types()",
            json_db,
            saurus_db,
            lambda db: db.get_prop_types(),
            lambda db: db.get_prop_types(),
        )
    )

    # videos_tag_get - all videos
    prop_types = json_db.get_prop_types()
    if prop_types:
        prop_name = prop_types[0]["name"]
        results.append(
            run_benchmark(
                f"videos_tag_get('{prop_name}') - all",
                json_db,
                saurus_db,
                lambda db: db.videos_tag_get(prop_name),
                lambda db: db.videos_tag_get(prop_name),
                iterations=3,
            )
        )

        # videos_tag_get - 100 videos
        results.append(
            run_benchmark(
                f"videos_tag_get('{prop_name}') - 100 videos",
                json_db,
                saurus_db,
                lambda db: db.videos_tag_get(prop_name, sample_100),
                lambda db: db.videos_tag_get(prop_name, sample_100),
            )
        )

    # videos_get_terms
    results.append(
        run_benchmark(
            "videos_get_terms()",
            json_db,
            saurus_db,
            lambda db: db.videos_get_terms(),
            lambda db: db.videos_get_terms(),
            iterations=3,
        )
    )

    return results


def run_write_benchmarks(get_json_db, get_saurus_db, all_video_ids):
    """Run write benchmarks using fresh database copies."""
    results = []

    print("  Write operations...")

    # ==========================================================================
    # Property write operations
    # ==========================================================================

    # Get property name
    json_db = get_json_db()
    prop_types = json_db.get_prop_types()
    prop_name = prop_types[0]["name"] if prop_types else "category"

    # videos_tag_set - single video
    def json_tag_set_1(db):
        db.videos_tag_set(prop_name, {all_video_ids[0]: ["benchmark_value"]})

    def saurus_tag_set_1(db):
        db.videos_tag_set(prop_name, {all_video_ids[0]: ["benchmark_value"]})

    result = BenchmarkResult("videos_tag_set() - 1 video")
    for _ in range(5):
        json_db = get_json_db()
        with timer():
            json_tag_set_1(json_db)
        result.json_times.append(timer.elapsed)

        saurus_db = get_saurus_db()
        with timer():
            saurus_tag_set_1(saurus_db)
        result.saurus_times.append(timer.elapsed)
    results.append(result)

    # videos_tag_set - 100 videos
    sample_100 = all_video_ids[:100]

    def json_tag_set_100(db):
        data = {vid: ["benchmark_value"] for vid in sample_100}
        db.videos_tag_set(prop_name, data)

    def saurus_tag_set_100(db):
        data = {vid: ["benchmark_value"] for vid in sample_100}
        db.videos_tag_set(prop_name, data)

    result = BenchmarkResult("videos_tag_set() - 100 videos")
    for _ in range(5):
        json_db = get_json_db()
        with timer():
            json_tag_set_100(json_db)
        result.json_times.append(timer.elapsed)

        saurus_db = get_saurus_db()
        with timer():
            saurus_tag_set_100(saurus_db)
        result.saurus_times.append(timer.elapsed)
    results.append(result)

    # videos_tag_set - 1000 videos
    sample_1000 = all_video_ids[:1000]

    def json_tag_set_1000(db):
        data = {vid: ["benchmark_value"] for vid in sample_1000}
        db.videos_tag_set(prop_name, data)

    def saurus_tag_set_1000(db):
        data = {vid: ["benchmark_value"] for vid in sample_1000}
        db.videos_tag_set(prop_name, data)

    result = BenchmarkResult("videos_tag_set() - 1000 videos")
    for _ in range(3):
        json_db = get_json_db()
        with timer():
            json_tag_set_1000(json_db)
        result.json_times.append(timer.elapsed)

        saurus_db = get_saurus_db()
        with timer():
            saurus_tag_set_1000(saurus_db)
        result.saurus_times.append(timer.elapsed)
    results.append(result)

    # videos_tag_set - ALL videos (10000)
    def json_tag_set_all(db):
        data = {vid: ["benchmark_value"] for vid in all_video_ids}
        db.videos_tag_set(prop_name, data)

    def saurus_tag_set_all(db):
        data = {vid: ["benchmark_value"] for vid in all_video_ids}
        db.videos_tag_set(prop_name, data)

    result = BenchmarkResult("videos_tag_set() - ALL 10000 videos")
    for _ in range(3):
        json_db = get_json_db()
        with timer():
            json_tag_set_all(json_db)
        result.json_times.append(timer.elapsed)

        saurus_db = get_saurus_db()
        with timer():
            saurus_tag_set_all(saurus_db)
        result.saurus_times.append(timer.elapsed)
    results.append(result)

    # ==========================================================================
    # Field write operations (videos_set_field)
    # ==========================================================================

    # videos_set_field - 100 videos (set watched)
    def json_set_field_100(db):
        db.videos_set_field("watched", {vid: True for vid in sample_100})

    def saurus_set_field_100(db):
        db.videos_set_field("watched", {vid: True for vid in sample_100})

    result = BenchmarkResult("videos_set_field(watched) - 100 videos")
    for _ in range(5):
        json_db = get_json_db()
        with timer():
            json_set_field_100(json_db)
        result.json_times.append(timer.elapsed)

        saurus_db = get_saurus_db()
        with timer():
            saurus_set_field_100(saurus_db)
        result.saurus_times.append(timer.elapsed)
    results.append(result)

    # videos_set_field - 1000 videos
    def json_set_field_1000(db):
        db.videos_set_field("watched", {vid: True for vid in sample_1000})

    def saurus_set_field_1000(db):
        db.videos_set_field("watched", {vid: True for vid in sample_1000})

    result = BenchmarkResult("videos_set_field(watched) - 1000 videos")
    for _ in range(3):
        json_db = get_json_db()
        with timer():
            json_set_field_1000(json_db)
        result.json_times.append(timer.elapsed)

        saurus_db = get_saurus_db()
        with timer():
            saurus_set_field_1000(saurus_db)
        result.saurus_times.append(timer.elapsed)
    results.append(result)

    # videos_set_field - ALL videos
    def json_set_field_all(db):
        db.videos_set_field("watched", {vid: True for vid in all_video_ids})

    def saurus_set_field_all(db):
        db.videos_set_field("watched", {vid: True for vid in all_video_ids})

    result = BenchmarkResult("videos_set_field(watched) - ALL 10000 videos")
    for _ in range(3):
        json_db = get_json_db()
        with timer():
            json_set_field_all(json_db)
        result.json_times.append(timer.elapsed)

        saurus_db = get_saurus_db()
        with timer():
            saurus_set_field_all(saurus_db)
        result.saurus_times.append(timer.elapsed)
    results.append(result)

    return results


def main():
    from saurus.sql.pysaurus_collection import PysaurusCollection
    from tests.utils import TEST_DB_FOLDER, TEST_HOME_DIR

    print("=" * 100)
    print("DATABASE BENCHMARK: JSON vs Saurus SQL (both on disk)")
    print("=" * 100)
    print()

    # ==========================================================================
    # Create temporary directories for both databases
    # ==========================================================================
    temp_base = tempfile.mkdtemp(prefix="pysaurus_benchmark_")
    print(f"Using temporary directory: {temp_base}")
    print()

    # Copy the entire home directory for JSON database
    temp_home = os.path.join(temp_base, "home_dir")
    shutil.copytree(TEST_HOME_DIR, temp_home, ignore=_ignore_sqlite_wal_files)

    # Copy just the test_database folder for Saurus SQL
    temp_saurus_folder = os.path.join(temp_base, "saurus_db")
    shutil.copytree(TEST_DB_FOLDER, temp_saurus_folder, ignore=_ignore_sqlite_wal_files)

    try:
        # ==========================================================================
        # Load databases (both from disk)
        # ==========================================================================
        print("Loading databases (from disk)...")

        with timer():
            from pysaurus.application.application import Application

            app = Application(home_dir=temp_home)
            json_db = app.open_database_from_name("test_database")
        json_load_time = timer.elapsed
        print(f"  JSON database loaded in {json_load_time * 1000:.2f}ms")

        with timer():
            saurus_db = PysaurusCollection(temp_saurus_folder)
        saurus_load_time = timer.elapsed
        print(f"  Saurus SQL database loaded in {saurus_load_time * 1000:.2f}ms")
        print()

        # Get sample data
        all_video_ids = [v.video_id for v in json_db.get_videos(include=["video_id"])]
        sample_100 = all_video_ids[:100]
        sample_1000 = all_video_ids[:1000]

        print(f"Total videos: {len(all_video_ids)}")
        print()

        results = []

        # ==========================================================================
        # Database loading result
        # ==========================================================================
        load_result = BenchmarkResult("Database loading (from disk)")
        load_result.json_times = [json_load_time]
        load_result.saurus_times = [saurus_load_time]
        results.append(load_result)

        # ==========================================================================
        # Read benchmarks (using the loaded databases)
        # With persistent=True in skullite, we can reuse the same instance
        # ==========================================================================
        print("Running read benchmarks (on disk)...")

        read_results = run_read_benchmarks(
            json_db, saurus_db, all_video_ids, sample_100, sample_1000
        )
        results.extend(read_results)

        # ==========================================================================
        # Write benchmarks (need fresh copies for each test)
        # ==========================================================================
        print()
        print("Running write benchmarks (on disk, fresh copies)...")

        def get_json_db_copy():
            """Create a fresh disk copy of JSON database."""
            copy_dir = tempfile.mkdtemp(prefix="json_copy_", dir=temp_base)
            copy_home = os.path.join(copy_dir, "home_dir")
            shutil.copytree(temp_home, copy_home, ignore=_ignore_sqlite_wal_files)
            from pysaurus.application.application import Application

            app = Application(home_dir=copy_home)
            return app.open_database_from_name("test_database")

        def saurus_db_copy():
            """Create a fresh disk copy of Saurus SQL database."""
            copy_dir = tempfile.mkdtemp(prefix="saurus_copy_", dir=temp_base)
            copy_folder = os.path.join(copy_dir, "db")
            shutil.copytree(
                temp_saurus_folder, copy_folder, ignore=_ignore_sqlite_wal_files
            )
            return PysaurusCollection(copy_folder)

        write_results = run_write_benchmarks(
            get_json_db_copy, saurus_db_copy, all_video_ids
        )
        results.extend(write_results)

    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_base, ignore_errors=True)
        except Exception:
            print(f"Warning: Could not fully clean up {temp_base}")

    # ==========================================================================
    # Print results
    # ==========================================================================
    print()
    print("=" * 100)
    print("RESULTS")
    print("=" * 100)
    print()

    print("READ OPERATIONS:")
    print("-" * 100)
    for result in results[: len(read_results) + 1]:  # +1 for loading
        print(result)

    print()
    print("WRITE OPERATIONS:")
    print("-" * 100)
    for result in results[len(read_results) + 1 :]:
        print(result)

    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)

    # Read summary
    read_only = results[1 : len(read_results) + 1]  # Exclude loading
    faster_saurus_read = sum(1 for r in read_only if r.speedup > 1)
    faster_json_read = sum(1 for r in read_only if r.speedup < 1)
    avg_read_speedup = statistics.mean(r.speedup for r in read_only if r.speedup > 0)

    print(f"READ:  Saurus faster in {faster_saurus_read}/{len(read_only)} benchmarks")
    print(f"       JSON faster in {faster_json_read}/{len(read_only)} benchmarks")
    print(f"       Average speedup: {avg_read_speedup:.2f}x")

    # Write summary
    write_only = results[len(read_results) + 1 :]
    faster_saurus_write = sum(1 for r in write_only if r.speedup > 1)
    faster_json_write = sum(1 for r in write_only if r.speedup < 1)
    avg_write_speedup = statistics.mean(r.speedup for r in write_only if r.speedup > 0)

    print()
    print(f"WRITE: Saurus faster in {faster_saurus_write}/{len(write_only)} benchmarks")
    print(f"       JSON faster in {faster_json_write}/{len(write_only)} benchmarks")
    print(f"       Average speedup: {avg_write_speedup:.2f}x")

    # Overall
    print()
    all_benchmarks = results[1:]  # Exclude loading
    avg_overall = statistics.mean(r.speedup for r in all_benchmarks if r.speedup > 0)
    print(f"OVERALL: Average speedup: {avg_overall:.2f}x")


if __name__ == "__main__":
    main()
