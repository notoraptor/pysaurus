from typing import Self


class _Source(list):
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

    MUTUALLY_EXCLUSIVE = {
        "discarded": ["allowed"],
        "allowed": ["discarded"],
        "readable": ["unreadable"],
        "unreadable": ["readable", "with_thumbnails", "without_thumbnails"],
        "found": ["not_found"],
        "not_found": ["found"],
        "with_thumbnails": ["unreadable", "without_thumbnails"],
        "without_thumbnails": ["unreadable", "with_thumbnails"],
    }

    def _get(self, flag: str) -> Self:
        assert flag in self.MUTUALLY_EXCLUSIVE
        self._append(flag, mutually_exclusive=self.MUTUALLY_EXCLUSIVE[flag])
        return self

    @property
    def discarded(self) -> Self:
        return self._get("discarded")

    @property
    def allowed(self) -> Self:
        return self._get("allowed")

    @property
    def readable(self) -> Self:
        return self._get("readable")

    @property
    def unreadable(self) -> Self:
        return self._get("unreadable")

    @property
    def found(self) -> Self:
        return self._get("found")

    @property
    def not_found(self) -> Self:
        return self._get("not_found")

    @property
    def with_thumbnails(self) -> Self:
        return self._get("with_thumbnails")

    @property
    def without_thumbnails(self) -> Self:
        return self._get("without_thumbnails")


class _SourceFactory:
    __slots__ = ()

    @property
    def discarded(self):
        return _Source().discarded

    @property
    def allowed(self):
        return _Source().allowed

    @property
    def readable(self):
        return _Source().readable

    @property
    def unreadable(self):
        return _Source().unreadable

    @property
    def found(self):
        return _Source().found

    @property
    def not_found(self):
        return _Source().not_found

    @property
    def with_thumbnails(self):
        return _Source().with_thumbnails

    @property
    def without_thumbnails(self):
        return _Source().without_thumbnails

    def all(self):
        sources = set()
        for flag in _Source.MUTUALLY_EXCLUSIVE:
            self._expand([flag], sources)
        for i, source in enumerate(sorted(sources)):
            print(i + 1, source)

    def _expand(self, source: list[str], sources: set):
        mu = _Source.MUTUALLY_EXCLUSIVE
        allowed_flags = set(mu)
        allowed_flags.difference_update(source)
        for source_flag in source:
            allowed_flags.difference_update(mu[source_flag])
        if allowed_flags:
            for allowed_flag in allowed_flags:
                self._expand(source + [allowed_flag], sources)
        else:
            sources.add(tuple(sorted(source)))


SOURCES = _SourceFactory()
