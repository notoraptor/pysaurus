"""
Tests for video_mega_source_count: counts distinct videos covered by the
union of several sources (each a set of ANDed flags), which is what
PysaurusCollection.query_videos exposes as output.source_count.
"""

import pytest

from pysaurus.database.saurus.pysaurus_connection import PysaurusConnection
from pysaurus.database.saurus.video_mega_search import video_mega_source_count
from pysaurus.dbview.view_context import ViewContext


@pytest.fixture
def db() -> PysaurusConnection:
    return PysaurusConnection(None)


def _insert(db: PysaurusConnection, filename: str, *, unreadable: int, is_file: int):
    db.modify(
        "INSERT INTO video (filename, unreadable, is_file) VALUES (?, ?, ?)",
        [filename, unreadable, is_file],
    )


@pytest.fixture
def four_videos(db: PysaurusConnection) -> PysaurusConnection:
    # One video per combination of readable/unreadable x found/not_found.
    _insert(db, "C:\\v\\readable_found.mp4", unreadable=0, is_file=1)
    _insert(db, "C:\\v\\readable_not_found.mp4", unreadable=0, is_file=0)
    _insert(db, "C:\\v\\unreadable_found.mp4", unreadable=1, is_file=1)
    _insert(db, "C:\\v\\unreadable_not_found.mp4", unreadable=1, is_file=0)
    return db


class TestVideoMegaSourceCount:
    def test_no_sources_returns_zero(self, four_videos):
        assert video_mega_source_count(four_videos, sources=[]) == 0

    def test_single_source(self, four_videos):
        assert video_mega_source_count(four_videos, sources=[["readable"]]) == 2
        assert video_mega_source_count(four_videos, sources=[["found"]]) == 2

    def test_single_source_with_multiple_flags_is_anded(self, four_videos):
        assert (
            video_mega_source_count(four_videos, sources=[["readable", "found"]]) == 1
        )

    def test_overlapping_sources_are_not_double_counted(self, four_videos):
        # readable = {readable_found, readable_not_found}
        # found = {readable_found, unreadable_found}
        # Their union has 3 distinct videos, not 4: readable_found is in both.
        assert (
            video_mega_source_count(four_videos, sources=[["readable"], ["found"]]) == 3
        )

    def test_disjoint_sources_sum_up(self, four_videos):
        # readable+found and unreadable+not_found never overlap.
        assert (
            video_mega_source_count(
                four_videos,
                sources=[["readable", "found"], ["unreadable", "not_found"]],
            )
            == 2
        )

    def test_all_four_combinations_cover_everything(self, four_videos):
        assert (
            video_mega_source_count(
                four_videos,
                sources=[
                    ["readable", "found"],
                    ["readable", "not_found"],
                    ["unreadable", "found"],
                    ["unreadable", "not_found"],
                ],
            )
            == 4
        )


def test_query_videos_source_count_matches_video_mega_source_count(mem_saurus_database):
    """End-to-end: PysaurusCollection.query_videos wires view.sources through
    to video_mega_source_count without altering the result."""
    view = ViewContext()
    view.set_sources([["readable"], ["found"]])

    output = mem_saurus_database.query_videos(view, page_size=10, page_number=0)

    assert output.source_count == video_mega_source_count(
        mem_saurus_database.db, sources=view.sources
    )
