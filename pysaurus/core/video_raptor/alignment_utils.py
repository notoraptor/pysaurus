from ctypes import c_int
from typing import Any, List

from pysaurus.core.video_raptor.structures import Sequence, c_int_p


def project(value, from_a, from_b, to_u, to_v):
    return ((value - from_a) * (to_v - to_u) / (from_b - from_a)) + to_u


class Miniature:
    __slots__ = ('identifier', 'r', 'g', 'b', 'i', 'width', 'height')

    def __init__(self, red, green, blue, width, height, identifier=None):
        # type: (List[int], List[int], List[int], int, int, Any) -> None
        self.r = red
        self.g = green
        self.b = blue
        self.i = list(range(width * height))
        self.width = width
        self.height = height
        self.identifier = identifier
        self.i.sort(key=lambda index: (self.r[index], self.g[index], self.b[index], index % width, index // width))

    def to_c_sequence(self, score=0.0, classification=-1):
        array_type = c_int * len(self.r)
        return Sequence(c_int_p(array_type(*self.r)),
                        c_int_p(array_type(*self.g)),
                        c_int_p(array_type(*self.b)),
                        c_int_p(array_type(*self.i)),
                        score, classification)
