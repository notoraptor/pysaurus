import pytest

from pysaurus.video.source_factory import SOURCES


def test_source_factory():
    assert SOURCES.readable == ["readable"]
    assert SOURCES.unreadable == ["unreadable"]
    assert SOURCES.found == ["found"]
    assert SOURCES.not_found == ["not_found"]
    assert SOURCES.with_thumbnails == ["with_thumbnails"]
    assert SOURCES.without_thumbnails == ["without_thumbnails"]

    with pytest.raises(ValueError, match="already added"):
        print(SOURCES.readable.readable)

    with pytest.raises(ValueError, match="already added"):
        print(SOURCES.readable.found.readable)

    with pytest.raises(ValueError, match="already added"):
        print(SOURCES.not_found.unreadable.unreadable)

    with pytest.raises(ValueError, match="already added"):
        print(SOURCES.found.readable.with_thumbnails.found)

    assert SOURCES.readable.found == ["readable", "found"]
    assert SOURCES.readable.found.with_thumbnails == [
        "readable",
        "found",
        "with_thumbnails",
    ]
    assert SOURCES.readable.found.without_thumbnails == [
        "readable",
        "found",
        "without_thumbnails",
    ]
    assert SOURCES.readable.not_found == ["readable", "not_found"]
    assert SOURCES.readable.not_found.with_thumbnails == [
        "readable",
        "not_found",
        "with_thumbnails",
    ]
    assert SOURCES.readable.not_found.without_thumbnails == [
        "readable",
        "not_found",
        "without_thumbnails",
    ]
    assert SOURCES.unreadable.found == ["unreadable", "found"]
    assert SOURCES.unreadable.not_found == ["unreadable", "not_found"]

    with pytest.raises(ValueError, match="cannot contain both"):
        print(SOURCES.readable.unreadable)

    with pytest.raises(ValueError, match="cannot contain both"):
        print(SOURCES.found.not_found)

    with pytest.raises(ValueError, match="cannot contain both"):
        print(SOURCES.with_thumbnails.without_thumbnails)

    with pytest.raises(ValueError, match="cannot contain both"):
        print(SOURCES.unreadable.with_thumbnails)

    with pytest.raises(ValueError, match="cannot contain both"):
        print(SOURCES.unreadable.without_thumbnails)
