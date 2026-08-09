"""The miniatures cache is stamped with the database version.

It stores raw path strings, so a file written before a migration that rewrote
paths (m0006 folds mount points) holds spellings that no longer match the
database. Nothing downstream can tell a stale spelling from a valid one --
compare_miniatures asserts on it -- so a file from another version is dropped
and regenerated lazily rather than read.
"""

import pytest
import ujson as json

from pysaurus.application import exceptions
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.miniature import Miniature
from pysaurus.database.algorithms.miniatures import Miniatures


@pytest.fixture
def miniature() -> Miniature:
    size = 2
    m = Miniature(
        b"\x01" * (size * size),
        b"\x02" * (size * size),
        b"\x03" * (size * size),
        size,
        size,
    )
    m.identifier = "C:\\Videos\\a.mkv"
    return m


@pytest.fixture
def path(tmp_path) -> AbsolutePath:
    return AbsolutePath.ensure(str(tmp_path / "miniatures.json"))


def test_absent_file_reads_as_empty(path):
    assert Miniatures.read_miniatures_file(path, 6) == {}


def test_round_trip_on_the_same_version(path, miniature):
    Miniatures.write_miniatures_file(path, 6, [miniature])
    stored = Miniatures.read_miniatures_file(path, 6)
    assert list(stored) == [AbsolutePath("C:\\Videos\\a.mkv")]


def test_another_version_is_dropped(path, miniature):
    Miniatures.write_miniatures_file(path, 5, [miniature])
    assert Miniatures.read_miniatures_file(path, 6) == {}
    assert not path.exists(), "the stale file must be gone, not merely ignored"


def test_the_pre_versioning_format_is_dropped(path, miniature):
    """Old files are a bare JSON array, with no version to compare."""
    with open(path.path, "w") as file:
        json.dump([miniature.to_dict()], file)
    assert Miniatures.read_miniatures_file(path, 6) == {}
    assert not path.exists()


def test_a_corrupt_file_is_dropped(path):
    """It is only a cache: unreadable means regenerate, not crash on open."""
    with open(path.path, "w") as file:
        file.write("{not json")
    assert Miniatures.read_miniatures_file(path, 6) == {}
    assert not path.exists()


def test_a_versioned_file_with_a_broken_body_still_raises(path):
    """A matching version but no entries is corruption, not staleness."""
    with open(path.path, "w") as file:
        json.dump({"version": 6, "miniatures": "not a list"}, file)
    with pytest.raises(exceptions.InvalidMiniaturesJSON):
        Miniatures.read_miniatures_file(path, 6)
