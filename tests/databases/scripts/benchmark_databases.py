"""
Benchmark comparing JSON database vs NewSQL database performance.

Run with: python tests/benchmark_databases.py
"""

import gc
import statistics
import time
from contextlib import contextmanager
from dataclasses import dataclass, field

from pysaurus.video.video_sorting import VideoSorting


@dataclass
class BenchmarkResult:
    """Result of a single benchmark."""

    name: str
    json_times: list[float] = field(default_factory=list)
    sql_times: list[float] = field(default_factory=list)

    @property
    def json_mean(self) -> float:
        return statistics.mean(self.json_times) if self.json_times else 0

    @property
    def sql_mean(self) -> float:
        return statistics.mean(self.sql_times) if self.sql_times else 0

    @property
    def speedup(self) -> float:
        if self.sql_mean == 0:
            return 0
        return self.json_mean / self.sql_mean

    def __str__(self) -> str:
        json_ms = self.json_mean * 1000
        sql_ms = self.sql_mean * 1000
        if self.speedup >= 1:
            speedup_str = f"SQL {self.speedup:.2f}x faster"
        else:
            speedup_str = f"JSON {1 / self.speedup:.2f}x faster"
        return f"{self.name:40} | JSON: {json_ms:8.2f}ms | SQL: {sql_ms:8.2f}ms | {speedup_str}"


@contextmanager
def timer():
    """Context manager to measure execution time."""
    gc.collect()
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    timer.elapsed = elapsed


def run_benchmark(
    name: str, json_db, sql_db, json_fn, sql_fn, iterations: int = 5
) -> BenchmarkResult:
    """Run a benchmark comparing JSON and SQL database."""
    result = BenchmarkResult(name)

    for _ in range(iterations):
        # Benchmark JSON
        with timer():
            json_fn(json_db)
        result.json_times.append(timer.elapsed)

        # Benchmark SQL
        with timer():
            sql_fn(sql_db)
        result.sql_times.append(timer.elapsed)

    return result


def main():
    from tests.utils import get_new_sql_database, get_old_app

    print("=" * 80)
    print("DATABASE BENCHMARK: JSON vs NewSQL")
    print("=" * 80)
    print()

    # Load databases
    print("Loading databases...")
    with timer():
        app = get_old_app()
        json_db = app.open_database_from_name("test_database")
    json_load_time = timer.elapsed
    print(f"  JSON database loaded in {json_load_time * 1000:.2f}ms")

    with timer():
        sql_db = get_new_sql_database()
    sql_load_time = timer.elapsed
    print(f"  SQL database loaded in {sql_load_time * 1000:.2f}ms")
    print()

    # Get some sample data for benchmarks
    all_video_ids = [v.video_id for v in json_db.get_videos(include=["video_id"])]
    sample_100 = all_video_ids[:100]
    sample_1000 = all_video_ids[:1000]

    print(f"Total videos: {len(all_video_ids)}")
    print()

    results = []

    # ==========================================================================
    # Database Loading (already measured)
    # ==========================================================================
    load_result = BenchmarkResult("Database loading")
    load_result.json_times = [json_load_time]
    load_result.sql_times = [sql_load_time]
    results.append(load_result)

    # ==========================================================================
    # Basic read operations
    # ==========================================================================
    print("Running benchmarks...")
    print("-" * 80)

    # count_videos
    results.append(
        run_benchmark(
            "count_videos()",
            json_db,
            sql_db,
            lambda db: db.ops.count_videos(),
            lambda db: db.ops.count_videos(),
        )
    )

    # get_videos() - all
    results.append(
        run_benchmark(
            "get_videos() - all 10k",
            json_db,
            sql_db,
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
            sql_db,
            lambda db: db.get_videos(where={"video_id": 500}),
            lambda db: db.get_videos(where={"video_id": 500}),
        )
    )

    # get_videos() - by video_id (100)
    results.append(
        run_benchmark(
            "get_videos(video_id=[...]) - 100 ids",
            json_db,
            sql_db,
            lambda db: db.get_videos(where={"video_id": sample_100}),
            lambda db: db.get_videos(where={"video_id": sample_100}),
        )
    )

    # get_videos() - with filter readable=True
    results.append(
        run_benchmark(
            "get_videos(readable=True)",
            json_db,
            sql_db,
            lambda db: list(db.get_videos(where={"readable": True})),
            lambda db: list(db.get_videos(where={"readable": True})),
            iterations=3,
        )
    )

    # get_videos() - with filter found=True
    results.append(
        run_benchmark(
            "get_videos(found=True)",
            json_db,
            sql_db,
            lambda db: list(db.get_videos(where={"found": True})),
            lambda db: list(db.get_videos(where={"found": True})),
            iterations=3,
        )
    )

    # ==========================================================================
    # Search operations
    # ==========================================================================

    # Search - single term AND
    results.append(
        run_benchmark(
            "search('test', 'and')",
            json_db,
            sql_db,
            lambda db: list(db.jsondb_provider_search("test", "and")),
            lambda db: list(db.jsondb_provider_search("test", "and")),
        )
    )

    # Search - multiple terms AND
    results.append(
        run_benchmark(
            "search('test 000001', 'and')",
            json_db,
            sql_db,
            lambda db: list(db.jsondb_provider_search("test 000001", "and")),
            lambda db: list(db.jsondb_provider_search("test 000001", "and")),
        )
    )

    # Search - OR condition
    results.append(
        run_benchmark(
            "search('action comedy', 'or')",
            json_db,
            sql_db,
            lambda db: list(db.jsondb_provider_search("action comedy", "or")),
            lambda db: list(db.jsondb_provider_search("action comedy", "or")),
        )
    )

    # Search - exact
    results.append(
        run_benchmark(
            "search('test_000500', 'exact')",
            json_db,
            sql_db,
            lambda db: list(db.jsondb_provider_search("test_000500", "exact")),
            lambda db: list(db.jsondb_provider_search("test_000500", "exact")),
        )
    )

    # Search - filtered by video IDs
    results.append(
        run_benchmark(
            "search('test', 'and', filtered 1000)",
            json_db,
            sql_db,
            lambda db: list(db.jsondb_provider_search("test", "and", sample_1000)),
            lambda db: list(db.jsondb_provider_search("test", "and", sample_1000)),
        )
    )

    # ==========================================================================
    # Sort operations
    # ==========================================================================

    sorting_title = VideoSorting(["title"])
    sorting_multi = VideoSorting(["width", "-height", "title"])

    # Sort - 100 videos by title
    results.append(
        run_benchmark(
            "sort(100 videos, by title)",
            json_db,
            sql_db,
            lambda db: db.jsondb_provider_sort_video_indices(sample_100, sorting_title),
            lambda db: db.jsondb_provider_sort_video_indices(sample_100, sorting_title),
        )
    )

    # Sort - 1000 videos by title
    results.append(
        run_benchmark(
            "sort(1000 videos, by title)",
            json_db,
            sql_db,
            lambda db: db.jsondb_provider_sort_video_indices(
                sample_1000, sorting_title
            ),
            lambda db: db.jsondb_provider_sort_video_indices(
                sample_1000, sorting_title
            ),
        )
    )

    # Sort - all videos by title
    results.append(
        run_benchmark(
            "sort(10000 videos, by title)",
            json_db,
            sql_db,
            lambda db: db.jsondb_provider_sort_video_indices(
                all_video_ids, sorting_title
            ),
            lambda db: db.jsondb_provider_sort_video_indices(
                all_video_ids, sorting_title
            ),
            iterations=3,
        )
    )

    # Sort - multi-field
    results.append(
        run_benchmark(
            "sort(1000 videos, multi-field)",
            json_db,
            sql_db,
            lambda db: db.jsondb_provider_sort_video_indices(
                sample_1000, sorting_multi
            ),
            lambda db: db.jsondb_provider_sort_video_indices(
                sample_1000, sorting_multi
            ),
        )
    )

    # ==========================================================================
    # Thumbnail operations
    # ==========================================================================

    from pysaurus.core.absolute_path import AbsolutePath

    sample_paths = [
        AbsolutePath(f) for f in [v.filename.path for v in json_db.get_videos()][:100]
    ]

    # has_thumbnail - 100 checks
    results.append(
        run_benchmark(
            "has_thumbnail() x 100",
            json_db,
            sql_db,
            lambda db: [db.jsondb_has_thumbnail(p) for p in sample_paths],
            lambda db: [db.jsondb_has_thumbnail(p) for p in sample_paths],
        )
    )

    # get_thumbnail_blob - 20 fetches
    sample_paths_20 = sample_paths[:20]
    results.append(
        run_benchmark(
            "get_thumbnail_blob() x 20",
            json_db,
            sql_db,
            lambda db: [db.jsondb_get_thumbnail_blob(p) for p in sample_paths_20],
            lambda db: [db.jsondb_get_thumbnail_blob(p) for p in sample_paths_20],
        )
    )

    # ==========================================================================
    # Property operations
    # ==========================================================================

    # get_prop_types
    results.append(
        run_benchmark(
            "get_prop_types()",
            json_db,
            sql_db,
            lambda db: db.get_prop_types(),
            lambda db: db.get_prop_types(),
        )
    )

    # videos_tag_get - all videos
    # First ensure there's a property to query
    prop_types = json_db.get_prop_types()
    if prop_types:
        prop_name = prop_types[0]["name"]
        results.append(
            run_benchmark(
                f"videos_tag_get('{prop_name}')",
                json_db,
                sql_db,
                lambda db: db.videos_tag_get(prop_name),
                lambda db: db.videos_tag_get(prop_name),
                iterations=3,
            )
        )

    # videos_get_terms (used for search index)
    results.append(
        run_benchmark(
            "videos_get_terms()",
            json_db,
            sql_db,
            lambda db: db.videos_get_terms(),
            lambda db: db.videos_get_terms(),
            iterations=3,
        )
    )

    # ==========================================================================
    # Print results
    # ==========================================================================
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    for result in results:
        print(result)

    print()
    print("-" * 80)

    # Summary statistics
    faster_sql = sum(1 for r in results if r.speedup > 1)
    faster_json = sum(1 for r in results if r.speedup < 1)
    avg_speedup = statistics.mean(r.speedup for r in results if r.speedup > 0)

    print(f"SQL faster in {faster_sql}/{len(results)} benchmarks")
    print(f"JSON faster in {faster_json}/{len(results)} benchmarks")
    print(f"Average speedup: {avg_speedup:.2f}x")

    # Close databases
    json_db.__close__()
    sql_db.__close__()


if __name__ == "__main__":
    main()
