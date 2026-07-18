"""
Tests for natural sorting in SQL: the *_numeric virtual fields order rows
through pysaurus_text_with_numbers(), whose self-delimiting encoding needs no
dataset-wide padding — so inserting a longer number later cannot break the
order (the old global-padding scheme did, until restart).
"""

import pytest

from pysaurus.database.saurus.grouping_utils import SqlFieldFactory
from pysaurus.database.saurus.pysaurus_connection import PysaurusConnection


@pytest.fixture
def db() -> PysaurusConnection:
    return PysaurusConnection(None)


def _insert(db: PysaurusConnection, filename: str, meta_title: str = "") -> None:
    db.modify(
        "INSERT INTO video (filename, meta_title) VALUES (?, ?)", [filename, meta_title]
    )


def _file_titles_sorted_naturally(db: PysaurusConnection) -> list[str]:
    order_by = SqlFieldFactory().get_sorting("file_title_numeric", False)
    return [
        row[0]
        for row in db.query(f"SELECT v.file_title FROM video AS v ORDER BY {order_by}")
    ]


class TestNaturalSortInSql:
    def test_numbers_sort_by_value_not_lexicographically(self, db):
        for name in ("e100", "e2", "e1", "e10"):
            _insert(db, f"C:\\v\\{name}.mp4")
        assert _file_titles_sorted_naturally(db) == ["e1", "e2", "e10", "e100"]

    def test_longer_number_inserted_later_keeps_order_correct(self, db):
        # The regression scenario of the old scheme: padding was computed from
        # the rows present at first query time and cached per db path, so a
        # row inserted afterwards with a longer number was mis-sorted.
        for name in ("e100", "e2"):
            _insert(db, f"C:\\v\\{name}.mp4")
        assert _file_titles_sorted_naturally(db) == ["e2", "e100"]
        _insert(db, "C:\\v\\e10000000.mp4")
        _insert(db, "C:\\v\\e3.mp4")
        assert _file_titles_sorted_naturally(db) == ["e2", "e3", "e100", "e10000000"]

    def test_title_numeric_prefers_meta_title(self, db):
        # meta_title "album 2" must rank before "album 10" even though the
        # filenames alone would give the opposite order.
        _insert(db, "C:\\v\\zzz9.mp4", meta_title="album 2")
        _insert(db, "C:\\v\\aaa.mp4", meta_title="album 10")
        order_by = SqlFieldFactory().get_sorting("title_numeric", False)
        rows = db.query_all(f"SELECT v.filename FROM video AS v ORDER BY {order_by}")
        assert [row[0] for row in rows] == ["C:\\v\\zzz9.mp4", "C:\\v\\aaa.mp4"]

    def test_filename_numeric_sorts_full_path(self, db):
        for name in ("part10", "part2", "part1"):
            _insert(db, f"C:\\v\\{name}.mp4")
        order_by = SqlFieldFactory().get_sorting("filename_numeric", False)
        rows = db.query_all(f"SELECT v.filename FROM video AS v ORDER BY {order_by}")
        assert [row[0] for row in rows] == [
            "C:\\v\\part1.mp4",
            "C:\\v\\part2.mp4",
            "C:\\v\\part10.mp4",
        ]
