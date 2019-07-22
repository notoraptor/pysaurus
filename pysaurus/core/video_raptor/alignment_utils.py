from ctypes import c_int
from typing import Any, List, Optional, Tuple

from pysaurus.core.video_raptor.structures import Sequence, c_int_p
from pysaurus.wip.image_utils import coord_to_flat, flat_to_coord, open_rgb_image


def project(value, from_a, from_b, to_u, to_v):
    return ((value - from_a) * (to_v - to_u) / (from_b - from_a)) + to_u


class Pixel:
    __slots__ = ('x', 'y', 'channels')

    def __init__(self, r, g, b, x, y):
        self.channels = (r, g, b)
        self.x = x
        self.y = y

    @property
    def r(self):
        return self.channels[0]

    @property
    def g(self):
        return self.channels[1]

    @property
    def b(self):
        return self.channels[2]

    def get_channels_order(self):
        return sorted(range(3), key=lambda i: (-self.channels[i], i))

    def __str__(self):
        return '[%d, %d, %d](%d, %d)' % (self.channels[0], self.channels[1], self.channels[2], self.x, self.y)

    def __hash__(self):
        return hash((self.r, self.g, self.b, self.x, self.y))

    def __eq__(self, other):
        # type: (Pixel) -> bool
        return self.r == other.r and self.g == other.g and self.b == other.b and self.x == other.x and self.y == other.y

    def __lt__(self, other):
        local_channels_order = self.get_channels_order()
        other_channels_order = other.get_channels_order()
        for i in range(3):
            if local_channels_order[i] < other_channels_order[i]:
                return True
            if local_channels_order[i] > other_channels_order[i]:
                return False
        local_c = tuple(self.channels[i] for i in local_channels_order)
        other_c = tuple(other.channels[i] for i in other_channels_order)
        if local_c < other_c:
            return True
        if local_c > other_c:
            return False
        local_d0 = self.x * self.x + self.y * self.y
        other_d0 = other.x * other.x + other.y * other.y
        if local_d0 < other_d0:
            return True
        if local_d0 > other_d0:
            return False
        return self.x < other.x


class Miniature:
    __slots__ = ('identifier', 'r', 'g', 'b', 'i', 'width', 'height')

    def compare(self, i, j):
        pass

    def get_pixel(self, index):
        x, y = flat_to_coord(index, self.width)
        return Pixel(self.r[index], self.g[index], self.b[index], x, y)

    def pixel_at(self, x, y):
        index = coord_to_flat(x, y, self.width)
        return Pixel(self.r[index], self.g[index], self.b[index], x, y)

    def coordinates_around(self, x, y, radius=1):
        coordinates = []
        for local_x in range(max(0, x - radius), min(x + radius, self.width - 1) + 1):
            for local_y in range(max(0, y - radius), min(y + radius, self.height - 1) + 1):
                coordinates.append((local_x, local_y))
        return coordinates

    def __init__(self, red, green, blue, width, height, identifier=None):
        # type: (List[int], List[int], List[int], int, int, Any) -> None
        self.r = red
        self.g = green
        self.b = blue
        self.i = [0]
        self.width = width
        self.height = height
        self.identifier = identifier

    def to_c_sequence(self, score=0.0, classification=-1):
        array_type = c_int * len(self.r)
        return Sequence(c_int_p(array_type(*self.r)),
                        c_int_p(array_type(*self.g)),
                        c_int_p(array_type(*self.b)),
                        c_int_p(array_type(*self.i)),
                        score, classification)

    @staticmethod
    def from_file_name(file_name, dimensions, identifier=None):
        # type: (str, Tuple[int, int], Optional[Any]) -> Miniature
        image = open_rgb_image(file_name)
        thumbnail = image.resize(dimensions)
        width, height = dimensions
        size = width * height
        red = [0] * size
        green = [0] * size
        blue = [0] * size
        for i, (r, g, b) in enumerate(thumbnail.getdata()):
            red[i] = r
            green[i] = g
            blue[i] = b
        return Miniature(red, green, blue, width, height, identifier)
