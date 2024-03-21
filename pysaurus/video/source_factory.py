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


class _SourceFactory:
    __slots__ = ()

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


SOURCES = _SourceFactory()
