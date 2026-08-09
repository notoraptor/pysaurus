"""The two selections of thumbnails to convert must stay interchangeable.

ensure_miniatures used to name every missing file in a WHERE IN, which SQLite
refuses past 32766 variables -- a real collection reaches that. The selection is
now a filter, and SaurusDatabaseAlgorithms overrides it only to stream the rows
instead of materializing them, so both must return the same pairs.
"""

import pytest

from pysaurus.database.database_algorithms import DatabaseAlgorithms


@pytest.fixture
def generic(example_saurus_database) -> DatabaseAlgorithms:
    """The portable implementation, which db.algos replaces with the SQL one."""
    return DatabaseAlgorithms(example_saurus_database)


def _paths(pairs) -> list:
    return sorted(path for path, _ in pairs)


def test_both_select_the_same_pairs(example_saurus_database, generic):
    assert sorted(generic._thumbnails_to_convert(set())) == sorted(
        example_saurus_database.algos._thumbnails_to_convert(set())
    )


def test_the_selection_is_readable_videos_with_a_thumbnail(
    example_saurus_database, generic
):
    """Pins the hand-written SQL to what the where clause means.

    The fixture holds unreadable videos, so the filter is not a no-op.
    """
    expected = sorted(
        video.filename
        for video in example_saurus_database.get_videos(
            include=["filename"], where={"readable": True, "with_thumbnails": True}
        )
    )
    assert expected, "fixture must offer something to convert"
    assert _paths(generic._thumbnails_to_convert(set())) == expected
    assert (
        _paths(example_saurus_database.algos._thumbnails_to_convert(set())) == expected
    )


def test_both_skip_the_same_known_files(example_saurus_database, generic):
    every_path = _paths(generic._thumbnails_to_convert(set()))
    done = set(every_path[::2])
    assert done and len(done) < len(every_path), "the split must exercise both sides"
    assert _paths(generic._thumbnails_to_convert(done)) == _paths(
        example_saurus_database.algos._thumbnails_to_convert(done)
    )
    assert not done & set(generic._thumbnails_to_convert(done))


def test_nothing_left_to_convert(example_saurus_database, generic):
    done = set(_paths(generic._thumbnails_to_convert(set())))
    assert generic._thumbnails_to_convert(done) == []
    assert example_saurus_database.algos._thumbnails_to_convert(done) == []


def test_thumbnails_come_back_as_bytes(example_saurus_database, generic):
    """get_miniatures feeds them to Miniature.from_file_data, which decodes."""
    for algos in (generic, example_saurus_database.algos):
        (_, thumbnail) = algos._thumbnails_to_convert(set())[0]
        assert isinstance(thumbnail, bytes) and thumbnail
