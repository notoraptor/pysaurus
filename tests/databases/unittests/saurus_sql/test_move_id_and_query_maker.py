"""
Tests for move_id grouping and QueryMaker (indirect).

These tests cover:
- _query_move_id_groups(): grouping by move_id with and without actual moves
- _filter_by_no_moves(): filtering videos without potential moves
- _filter_by_selected_field_group(): selecting the NULL move_id group
- QueryMaker (indirectly): tested through grouping + pagination + sorting + search,
  which exercises QueryMaker.copy(), .to_sql(), .add_field(), .add_left_join(),
  .order_by_complex(), .where, .set_fields(), .find_table(), .limit, .offset
"""

import pytest

from pysaurus.database.saurus.sql.pysaurus_collection import PysaurusCollection
from pysaurus.video_provider.view_context import ViewContext
from tests.conftest import EXAMPLE_DB_FOLDER
from tests.utils import get_saurus_sql_database


@pytest.fixture
def saurus_database() -> PysaurusCollection:
    return get_saurus_sql_database(EXAMPLE_DB_FOLDER)


class TestMoveIdGrouping:
    """Tests for grouping by move_id field."""

    def _query_ids(self, db, view) -> list[int]:
        return [v.video_id for v in db.query_videos(view, None, None).result]

    def _query_stats(self, db, view):
        return db.query_videos(view, 1, 0).classifier_stats

    def test_grouping_by_move_id_no_moves(self, saurus_database):
        """When no videos have potential moves, all go into the NULL group."""
        view = ViewContext()
        view.set_grouping("move_id", allow_singletons=True)
        indices = self._query_ids(saurus_database, view)
        stats = self._query_stats(saurus_database, view)

        # With 90 videos and no moves, there should be one NULL group
        assert len(indices) == 90
        assert len(stats) == 1
        assert stats[0].value is None
        assert stats[0].count == 90

    def test_grouping_by_move_id_select_null_group(self, saurus_database):
        """Selecting the NULL move_id group returns all videos without moves.

        This exercises _filter_by_no_moves().
        """
        view = ViewContext()
        view.set_grouping("move_id", allow_singletons=True)
        view.set_group(0)
        indices = self._query_ids(saurus_database, view)
        assert len(indices) == 90

    def test_grouping_by_move_id_without_singletons(self, saurus_database):
        """move_id grouping without singletons keeps groups with count > 1."""
        view = ViewContext()
        view.set_grouping("move_id", allow_singletons=False)
        stats = self._query_stats(saurus_database, view)

        # The NULL group has 90 videos, so it should still appear
        assert len(stats) == 1
        assert stats[0].count == 90

    def test_grouping_by_move_id_with_sorting(self, saurus_database):
        """move_id grouping respects sorting parameter."""
        view = ViewContext()

        view.set_grouping("move_id", allow_singletons=True, sorting="count")
        stats = self._query_stats(saurus_database, view)
        assert len(stats) == 1

        view.set_grouping(
            "move_id", allow_singletons=True, sorting="count", reverse=True
        )
        stats_rev = self._query_stats(saurus_database, view)
        assert len(stats_rev) == 1

    def test_grouping_by_move_id_with_source_filter(self, saurus_database):
        """move_id grouping works correctly with source filtering."""
        view = ViewContext()
        view.set_sources([["not_found"]])
        view.set_grouping("move_id", allow_singletons=True)
        stats = self._query_stats(saurus_database, view)

        total = sum(s.count for s in stats)
        assert total == 3

    def test_grouping_by_move_id_with_search(self, saurus_database):
        """move_id grouping combined with text search."""
        view = ViewContext()
        view.set_grouping("move_id", allow_singletons=True)
        view.set_search("palm", "and")
        indices = self._query_ids(saurus_database, view)

        assert len(indices) > 0
        assert len(indices) < 90

    def test_grouping_by_move_id_with_simulated_moves(self, saurus_database):
        """Simulate videos with potential moves by modifying the database.

        Creates a scenario where two videos share file_size/duration/duration_time_base
        but one is found and the other is not, which triggers actual move groups.
        This exercises _query_move_id_groups() with non-NULL groups and
        _filter_by_no_moves() / _filter_by_selected_field_group() for group selection.
        """
        db_conn = saurus_database.db

        # Pick two readable videos
        videos = db_conn.query_all(
            "SELECT video_id, file_size, duration, duration_time_base "
            "FROM video WHERE unreadable = 0 AND discarded = 0 AND is_file = 1 "
            "LIMIT 2"
        )
        assert len(videos) >= 2
        vid1, vid2 = videos[0], videos[1]

        # Make vid2 share file_size/duration/duration_time_base with vid1,
        # and mark it as not found (is_file = 0).
        # duration_time_base_not_null is a generated column from duration_time_base.
        with db_conn:
            db_conn.modify(
                "UPDATE video SET file_size = ?, duration = ?, "
                "duration_time_base = ?, is_file = 0 "
                "WHERE video_id = ?",
                [vid1[1], vid1[2], vid1[3], vid2[0]],
            )

        view = ViewContext()
        view.set_grouping("move_id", allow_singletons=True)
        stats = self._query_stats(saurus_database, view)

        # Should now have at least 2 groups: one non-NULL (the move pair) and NULL
        non_null_stats = [s for s in stats if s.value is not None]
        null_stats = [s for s in stats if s.value is None]
        assert len(non_null_stats) >= 1, "Expected at least one non-NULL move group"
        assert len(null_stats) == 1, "Expected exactly one NULL group"

        # The non-NULL group should contain exactly 2 videos (the pair)
        assert non_null_stats[0].count == 2

        # Select the non-NULL group and verify we get the right videos
        non_null_idx = next(i for i, s in enumerate(stats) if s.value is not None)
        view.set_group(non_null_idx)
        indices = self._query_ids(saurus_database, view)
        assert len(indices) == 2
        assert set(indices) == {vid1[0], vid2[0]}

        # Select the NULL group (videos without moves)
        null_idx = next(i for i, s in enumerate(stats) if s.value is None)
        view.set_group(null_idx)
        indices_null = self._query_ids(saurus_database, view)
        assert vid1[0] not in indices_null
        assert vid2[0] not in indices_null


class TestQueryMakerIndirect:
    """Indirect tests for QueryMaker through video_mega_group().

    QueryMaker is only used in video_mega_group() and _compute_results_and_stats().
    These tests exercise its key operations:
    - Construction: QueryMaker("video", "v"), add_field(), add_left_join()
    - Copying: .copy() for count/select/page variants
    - SQL generation: .to_sql() -> (query, params)
    - WHERE clause: .where.append_query(), .where.append_field(), .where.clear()
    - ORDER BY: .order_by_complex()
    - Field management: .set_field(), .set_fields(), .find_table()
    """

    def _query_ids(self, db, view) -> list[int]:
        return [v.video_id for v in db.query_videos(view, None, None).result]

    def test_grouping_with_pagination(self, saurus_database):
        """Pagination triggers QueryMaker.copy() 4 times and exercises
        limit/offset, set_field(COUNT), set_fields(SUM), find_table().
        """
        view = ViewContext()
        view.set_grouping("audio_codec", allow_singletons=True)

        state = saurus_database.query_videos(view, 5, 0)
        assert state.view_count > 0
        assert len(state.result) <= 5
        assert state.nb_pages >= 1

        # Second page
        state2 = saurus_database.query_videos(view, 5, 1)
        if state.nb_pages > 1:
            assert len(state2.result) > 0
            # Videos on page 2 should differ from page 1
            ids_p1 = {v.video_id for v in state.result}
            ids_p2 = {v.video_id for v in state2.result}
            assert ids_p1.isdisjoint(ids_p2)

    def test_grouping_with_sorting_exercises_order_by(self, saurus_database):
        """Sorting exercises QueryMaker.order_by_complex()."""
        view = ViewContext()
        view.set_grouping("audio_codec", allow_singletons=True)
        view.set_sort(["file_title"])
        indices_asc = self._query_ids(saurus_database, view)

        view.set_sort(["-file_title"])
        indices_desc = self._query_ids(saurus_database, view)

        assert indices_asc == list(reversed(indices_desc))

    def test_grouping_with_search_exercises_where(self, saurus_database):
        """Search + grouping exercises multiple WHERE clauses on QueryMaker."""
        view = ViewContext()
        view.set_grouping("audio_codec", allow_singletons=True)
        view.set_search("palm", "and")
        indices = self._query_ids(saurus_database, view)

        assert len(indices) > 0
        assert len(indices) < 90

    def test_id_search_exercises_early_return_path(self, saurus_database):
        """ID search exercises QueryMaker.where.append_field() and early return."""
        view = ViewContext()
        view.set_search("196", "id")
        indices = self._query_ids(saurus_database, view)

        assert indices == [196]

    def test_grouping_stats_exercises_set_fields(self, saurus_database):
        """query_videos returns stats (file_size, duration, count)
        computed via QueryMaker copies with set_fields(SUM, COUNT).
        """
        view = ViewContext()
        view.set_grouping("audio_codec", allow_singletons=True)
        state = saurus_database.query_videos(view, 100, 0)

        assert state.selection_file_size is not None
        assert state.selection_duration is not None
        assert state.view_count > 0
        assert state.selection_count > 0

    def test_source_filter_with_grouping_and_pagination(self, saurus_database):
        """Complex pipeline: source filter + grouping + pagination + sorting.

        Exercises the full QueryMaker lifecycle.
        """
        view = ViewContext()
        view.set_sources([["readable", "with_thumbnails"]])
        view.set_grouping("video_codec", allow_singletons=True)
        view.set_sort(["file_size"])

        state = saurus_database.query_videos(view, 10, 0)
        assert state.view_count > 0
        assert len(state.result) <= 10

        # Verify sorting: file_size should be non-decreasing
        sizes = [v.file_size for v in state.result]
        assert sizes == sorted(sizes)

    def test_empty_result_exercises_zero_query_path(self, saurus_database):
        """When grouping results in no groups, QueryMaker adds WHERE 0."""
        view = ViewContext()
        view.set_sources([["readable", "without_thumbnails"]])
        view.set_grouping("audio_codec")

        indices = self._query_ids(saurus_database, view)
        assert len(indices) == 0

        state = saurus_database.query_videos(view, 10, 0)
        assert state.view_count == 0
        assert len(state.result) == 0

    def test_left_join_thumbnail_exercises_find_table(self, saurus_database):
        """Video retrieval with thumbnail data exercises the LEFT JOIN
        and find_table("video_thumbnail") in QueryMaker.
        """
        view = ViewContext()
        state = saurus_database.query_videos(view, 5, 0)

        # Videos should have thumbnail-related fields
        for video in state.result:
            assert hasattr(video, "with_thumbnails")
