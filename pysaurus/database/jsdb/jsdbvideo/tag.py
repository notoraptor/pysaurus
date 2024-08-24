from typing import Any


class Tag:
    __slots__ = ("t",)

    def __init__(self, key: str, value: Any):
        self.t = (key, value)

    key = property(lambda self: self.t[0])
    val = property(lambda self: self.t[1])

    def __str__(self):
        return f"{type(self).__name__}{self.t}"

    __repr__ = __str__

    def __bool__(self):
        return self.val

    def __hash__(self):
        return hash(self.t)

    def __eq__(self, other):
        return self.t == other.t

    def __lt__(self, other):
        return self.t < other.t


class Term(Tag):
    __slots__ = ()

    def __init__(self, val):
        super().__init__("", val)
