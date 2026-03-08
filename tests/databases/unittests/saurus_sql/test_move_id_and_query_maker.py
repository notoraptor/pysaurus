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
from tests.conftest import EXAMPLE_DB_FOLDER
from tests.utils import get_saurus_sql_database


@pytest.fixture
def saurus_database() -> PysaurusCollection:
    return get_saurus_sql_database(EXAMPLE_DB_FOLDER)


class TestMoveIdGrouping:
    """Tests for grouping by move_id field."""

    def test_grouping_by_move_id_no_moves(self, saurus_database):
        """When no videos have potential moves, all go into the NULL group."""
        provider = saurus_database.provider
        provider.set_groups("move_id", allow_singletons=True)
        indices = provider.get_view_indices()  # triggers update
        group_def = provider.get_group_def()

        # With 90 videos and no moves, there should be one NULL group
        assert len(indices) == 90
        assert len(group_def["groups"]) == 1
        assert group_def["groups"][0]["value"] is None
        assert group_def["groups"][0]["count"] == 90

    def test_grouping_by_move_id_select_null_group(self, saurus_database):
        """Selecting the NULL move_id group returns all videos without moves.

        This exercises _filter_by_no_moves().
        """
        provider = saurus_database.provider
        provider.set_groups("move_id", allow_singletons=True)
        provider.set_group(0)
        indices = provider.get_view_indices()
        assert len(indices) == 90

    def test_grouping_by_move_id_without_singletons(self, saurus_database):
        """move_id grouping without singletons keeps groups with count > 1."""
        provider = saurus_database.provider
        provider.set_groups("move_id", allow_singletons=False)
        provider.get_view_indices()  # triggers update
        group_def = provider.get_group_def()

        # The NULL group has 90 videos, so it should still appear
        assert len(group_def["groups"]) == 1
        assert group_def["groups"][0]["count"] == 90

    def test_grouping_by_move_id_with_sorting(self, saurus_database):
        """move_id grouping respects sorting parameter."""
        provider = saurus_database.provider

        provider.set_groups("move_id", allow_singletons=True, sorting="count")
        provider.get_view_indices()
        group_def = provider.get_group_def()
        assert len(group_def["groups"]) == 1

        provider.set_groups(
            "move_id", allow_singletons=True, sorting="count", reverse=True
        )
        provider.get_view_indices()
        group_def_rev = provider.get_group_def()
        assert len(group_def_rev["groups"]) == 1

    def test_grouping_by_move_id_with_source_filter(self, saurus_database):
        """move_id grouping works correctly with source filtering."""
        provider = saurus_database.provider
        provider.set_sources([["not_found"]])
        provider.set_groups("move_id", allow_singletons=True)
        provider.get_view_indices()
        group_def = provider.get_group_def()

        total = sum(g["count"] for g in group_def["groups"])
        assert total == 3

    def test_grouping_by_move_id_with_search(self, saurus_database):
        """move_id grouping combined with text search."""
        provider = saurus_database.provider
        provider.set_groups("move_id", allow_singletons=True)
        provider.set_search("palm", "and")
        indices = provider.get_view_indices()

        assert len(indices) > 0
        assert len(indices) < 90

    def test_grouping_by_move_id_with_simulated_moves(self, saurus_database):
        """Simulate videos with potential moves by modifying the database.

        Creates a scenario where two videos share file_size/duration/duration_time_base
        but one is found and the other is not, which triggers actual move groups.
        This exercises _query_move_id_groups() with non-NULL groups and
        _filter_by_no_moves() / _filter_by_selected_field_group() for group selection.
        """
        db = saurus_database.db

        # Pick two readable videos
        videos = db.query_all(
            "SELECT video_id, file_size, duration, duration_time_base "
            "FROM video WHERE unreadable = 0 AND discarded = 0 AND is_file = 1 "
            "LIMIT 2"
        )
        assert len(videos) >= 2
        vid1, vid2 = videos[0], videos[1]

        # Make vid2 share file_size/duration/duration_time_base with vid1,
        # and mark it as not found (is_file = 0).
        # duration_time_base_not_null is a generated column from duration_time_base.
        with db:
            db.modify(
                "UPDATE video SET file_size = ?, duration = ?, "
                "duration_time_base = ?, is_file = 0 "
                "WHERE video_id = ?",
                [vid1[1], vid1[2], vid1[3], vid2[0]],
            )

        provider = saurus_database.provider
        provider.set_groups("move_id", allow_singletons=True)
        provider.get_view_indices()  # triggers update
        group_def = provider.get_group_def()

        # Should now have at least 2 groups: one non-NULL (the move pair) and NULL
        non_null_groups = [g for g in group_def["groups"] if g["value"] is not None]
        null_groups = [g for g in group_def["groups"] if g["value"] is None]
        assert len(non_null_groups) >= 1, "Expected at least one non-NULL move group"
        assert len(null_groups) == 1, "Expected exactly one NULL group"

        # The non-NULL group should contain exactly 2 videos (the pair)
        assert non_null_groups[0]["count"] == 2

        # Select the non-NULL group and verify we get the right videos
        non_null_idx = group_def["groups"].index(non_null_groups[0])
        provider.set_group(non_null_idx)
        indices = provider.get_view_indices()
        assert len(indices) == 2
        assert set(indices) == {vid1[0], vid2[0]}

        # Select the NULL group (videos without moves)
        null_idx = group_def["groups"].index(null_groups[0])
        provider.set_group(null_idx)
        indices_null = provider.get_view_indices()
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

    def test_grouping_with_pagination(self, saurus_database):
        """Pagination triggers QueryMaker.copy() 4 times and exercises
        limit/offset, set_field(COUNT), set_fields(SUM), find_table().
        """
        provider = saurus_database.provider
        provider.set_groups("audio_codec", allow_singletons=True)

        state = provider.get_current_state(page_size=5, page_number=0)
        assert state.view_count > 0
        assert len(state.result) <= 5
        assert state.nb_pages >= 1

        # Second page
        state2 = provider.get_current_state(page_size=5, page_number=1)
        if state.nb_pages > 1:
            assert len(state2.result) > 0
            # Videos on page 2 should differ from page 1
            ids_p1 = {v.video_id for v in state.result}
            ids_p2 = {v.video_id for v in state2.result}
            assert ids_p1.isdisjoint(ids_p2)

    def test_grouping_with_sorting_exercises_order_by(self, saurus_database):
        """Sorting exercises QueryMaker.order_by_complex()."""
        provider = saurus_database.provider
        provider.set_groups("audio_codec", allow_singletons=True)
        provider.set_sort(["file_title"])
        indices_asc = provider.get_view_indices()

        provider.set_sort(["-file_title"])
        indices_desc = provider.get_view_indices()

        assert indices_asc == list(reversed(indices_desc))

    def test_grouping_with_search_exercises_where(self, saurus_database):
        """Search + grouping exercises multiple WHERE clauses on QueryMaker."""
        provider = saurus_database.provider
        provider.set_groups("audio_codec", allow_singletons=True)
        provider.set_search("palm", "and")
        indices = provider.get_view_indices()

        assert len(indices) > 0
        assert len(indices) < 90

    def test_id_search_exercises_early_return_path(self, saurus_database):
        """ID search exercises QueryMaker.where.append_field() and early return."""
        provider = saurus_database.provider
        provider.set_search("196", "id")
        indices = provider.get_view_indices()

        assert indices == [196]

    def test_grouping_stats_exercises_set_fields(self, saurus_database):
        """get_current_state returns stats (file_size, duration, count)
        computed via QueryMaker copies with set_fields(SUM, COUNT).
        """
        provider = saurus_database.provider
        provider.set_groups("audio_codec", allow_singletons=True)
        state = provider.get_current_state(page_size=100, page_number=0)

        assert state.selection_file_size is not None
        assert state.selection_duration is not None
        assert state.view_count > 0
        assert state.selection_count > 0

    def test_source_filter_with_grouping_and_pagination(self, saurus_database):
        """Complex pipeline: source filter + grouping + pagination + sorting.

        Exercises the full QueryMaker lifecycle.
        """
        provider = saurus_database.provider
        provider.set_sources([["readable", "with_thumbnails"]])
        provider.set_groups("video_codec", allow_singletons=True)
        provider.set_sort(["file_size"])

        state = provider.get_current_state(page_size=10, page_number=0)
        assert state.view_count > 0
        assert len(state.result) <= 10

        # Verify sorting: file_size should be non-decreasing
        sizes = [v.file_size for v in state.result]
        assert sizes == sorted(sizes)

    def test_empty_result_exercises_zero_query_path(self, saurus_database):
        """When grouping results in no groups, QueryMaker adds WHERE 0."""
        provider = saurus_database.provider
        provider.set_sources([["readable", "without_thumbnails"]])
        provider.set_groups("audio_codec")

        indices = provider.get_view_indices()
        assert len(indices) == 0

        state = provider.get_current_state(page_size=10, page_number=0)
        assert state.view_count == 0
        assert len(state.result) == 0

    def test_left_join_thumbnail_exercises_find_table(self, saurus_database):
        """Video retrieval with thumbnail data exercises the LEFT JOIN
        and find_table("video_thumbnail") in QueryMaker.
        """
        provider = saurus_database.provider
        state = provider.get_current_state(page_size=5, page_number=0)

        # Videos should have thumbnail-related fields
        for video in state.result:
            assert hasattr(video, "with_thumbnails")
