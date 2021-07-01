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


def categorize_position(x, y, width, step):
    return int(y // step) * (width // step) + int(x // step)


def categorize_value(x, step):
    return int(x // step)


def categorize_sub_position(x, y, width, step):
    p_x = categorize_sub_value(x, step)
    p_y = categorize_sub_value(y, step)
    return p_y * (1 + width // step) + p_x


def categorize_sub_value(x, step):
    return int((int(x // (step // 2)) + 1) // 2)
