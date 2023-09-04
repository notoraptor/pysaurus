from typing import Set, Tuple

from pysaurus.core import functions
from pysaurus.core.linear_regression import LinearRegression


class PixelGroup:
    __slots__ = "color", "image_width", "identifier", "members"

    def __init__(
        self,
        color: Tuple[float, float, float],
        image_width: int,
        identifier: int,
        members: Set[int],
    ):
        self.color = color
        self.image_width = image_width
        self.identifier = identifier
        self.members = members

    def __str__(self):
        return (
            f"{type(self).__name__}({self.identifier + 1}, "
            f"{self.color}, "
            f"{len(self.members)} member(s), "
            f"center {self.center})"
        )

    def __hash__(self):
        return hash(self.identifier)

    def __eq__(self, other):
        return self.identifier == other.identifier

    @property
    def center(self):
        nb_points = len(self.members)
        total_x = 0
        total_y = 0
        for identifier in self.members:
            x, y = functions.flat_to_coord(identifier, self.image_width)
            total_x += x
            total_y += y
        return total_x / nb_points, total_y / nb_points

    @property
    def rect(self) -> Tuple[int, int, int, int]:
        """Return (x, y, width, height)"""
        positions = [functions.flat_to_coord(i, self.image_width) for i in self.members]
        min_x = min(pos[0] for pos in positions)
        min_y = min(pos[1] for pos in positions)
        max_x = max(pos[0] for pos in positions)
        max_y = max(pos[1] for pos in positions)
        return (min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)

    @property
    def linear_regression(self):
        positions = [functions.flat_to_coord(i, self.image_width) for i in self.members]
        xs = [pos[0] for pos in positions]
        ys = [pos[1] for pos in positions]
        a, b, r = LinearRegression.linear_regression(xs, ys)
        return a, b, r
