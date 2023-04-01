from typing import Any


class Tag:
    __slots__ = ("tag",)

    def __init__(self, key: str, value: Any):
        self.tag = (key, value)

    key = property(lambda self: self.tag[0])
    val = property(lambda self: self.tag[1])

    def __str__(self):
        return f"{type(self).__name__}{self.tag}"

    __repr__ = __str__

    def __bool__(self):
        return self.val

    def __hash__(self):
        return hash(self.tag)

    def __eq__(self, other):
        return self.tag == other.tag

    def __lt__(self, other):
        return self.tag < other.tag


class Term(Tag):
    __slots__ = ()

    def __init__(self, val):
        super().__init__("", val)
