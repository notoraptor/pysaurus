from ctypes import c_int
from typing import Any, List
import functools
from pysaurus.core.video_raptor.structures import Sequence, c_int_p


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
        return Pixel(self.r[index], self.g[index], self.b[index], index % self.width, index // self.width)

    def __init__(self, red, green, blue, width, height, identifier=None):
        # type: (List[int], List[int], List[int], int, int, Any) -> None
        self.r = red
        self.g = green
        self.b = blue
        self.i = list(range(width * height))
        self.width = width
        self.height = height
        self.identifier = identifier
        self.i.sort(key=lambda index: self.get_pixel(index))
        # for i in self.i:
        #     pixel = self.get_pixel(i)
        #     print(pixel, pixel.get_channels_order())
        # exit(0)

    def to_c_sequence(self, score=0.0, classification=-1):
        array_type = c_int * len(self.r)
        return Sequence(c_int_p(array_type(*self.r)),
                        c_int_p(array_type(*self.g)),
                        c_int_p(array_type(*self.b)),
                        c_int_p(array_type(*self.i)),
                        score, classification)
