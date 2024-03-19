from typing import List
import pytest


class Source(list):
    def __init__(self):
        super().__init__()
        self.__seen = set()

    def _append(self, flag: str, mutually_exclusive: list = None):
        if mutually_exclusive is not None:
            for unexpected in mutually_exclusive:
                if unexpected in self.__seen:
                    raise ValueError(
                        f"Source cannot contain both {unexpected} and {flag}"
                    )
        if flag in self.__seen:
            raise ValueError(f"Source flag already added: {flag}")
        self.__seen.add(flag)
        self.append(flag)

    @property
    def readable(self):
        self._append("readable", mutually_exclusive=["unreadable"])
        return self

    @property
    def unreadable(self):
        self._append(
            "unreadable",
            mutually_exclusive=["readable", "with_thumbnails", "without_thumbnails"],
        )
        return self

    @property
    def found(self):
        self._append("found", mutually_exclusive=["not_found"])
        return self

    @property
    def not_found(self):
        self._append("not_found", mutually_exclusive=["found"])
        return self

    @property
    def with_thumbnails(self):
        self._append(
            "with_thumbnails", mutually_exclusive=["unreadable", "without_thumbnails"]
        )
        return self

    @property
    def without_thumbnails(self):
        self._append(
            "without_thumbnails", mutually_exclusive=["unreadable", "with_thumbnails"]
        )
        return self


class SourceFactory:
    @property
    def readable(self):
        return Source().readable

    @property
    def unreadable(self):
        return Source().unreadable

    @property
    def found(self):
        return Source().found

    @property
    def not_found(self):
        return Source().not_found

    @property
    def with_thumbnails(self):
        return Source().with_thumbnails

    @property
    def without_thumbnails(self):
        return Source().without_thumbnails


SOURCES = SourceFactory()


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
