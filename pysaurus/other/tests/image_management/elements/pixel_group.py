from typing import Tuple, Set

from pysaurus.core import functions
from pysaurus.other.tests.image_management.elements.basic_group import BasicGroup
from pysaurus.other.tests.image_management.elements.spaced_points import SpacedPoints


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

    def to_basic_group(
        self,
        spaced_color: SpacedPoints,
        spaced_position: SpacedPoints,
        spaced_size: SpacedPoints,
    ):
        color = tuple(spaced_color.nearest_point(value) for value in self.color)
        center = tuple(spaced_position.nearest_point(value) for value in self.center)
        size = spaced_size.nearest_point(len(self.members))
        return BasicGroup(color, center, size)

    def to_basic_group_intervals(
        self, nb_color_points, nb_position_points, nb_size_points
    ):
        color = tuple(
            categorize_value(value, 256 // nb_color_points) for value in self.color
        )
        center = categorize_position(*self.center, 32, 32 // nb_position_points)
        size = categorize_value(len(self.members), 1024 // nb_size_points)
        return BasicGroup(color, center, size)

    def to_basic_group_sub_intervals(
        self, nb_color_points, nb_position_points, nb_size_points
    ):
        color = tuple(
            categorize_sub_value(value, 256 // nb_color_points) for value in self.color
        )
        center = categorize_sub_position(*self.center, 32, 32 // nb_position_points)
        size = categorize_sub_value(len(self.members), 1024 // nb_size_points)
        return BasicGroup(color, center, size)

    def to_basic_group_raw(self):
        return BasicGroup(self.color, self.center, len(self.members))

    def to_basic_group_intervals_alt(
        self, nb_color_points, nb_position_points, nb_size_points
    ):
        cil = 256 // nb_color_points
        pil = 32 // nb_position_points
        sil = 1024 // nb_size_points
        color = tuple(int(value // cil) * cil for value in self.color)
        center = tuple(int(value // pil) * pil for value in self.center)
        size = int(len(self.members) // sil) * sil
        return BasicGroup(color, center, size)
