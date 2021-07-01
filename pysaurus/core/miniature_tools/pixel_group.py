from typing import Tuple, Set

from pysaurus.core import functions


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
            f"PixelGroup({self.identifier + 1} "
            f"{self.color}, "
            f"{len(self.members)} member{functions.get_plural_suffix(len(self.members))}, "
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
