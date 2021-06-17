from typing import Tuple


class BasicGroup:
    __slots__ = "color", "center", "size"

    def __init__(self, color: Tuple, center: Tuple, size: int):
        self.color = color
        self.center = center
        self.size = size

    key = property(lambda self: (self.color, self.center, self.size))

    def __str__(self):
        return str(self.key)

    def __repr__(self):
        return repr(self.key)

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key

    def __lt__(self, other):
        return self.key < other.key
