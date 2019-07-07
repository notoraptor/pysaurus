from ctypes import c_int
from typing import Any, List

from pysaurus.core.video_raptor.structures import Sequence, c_int_p


class Miniature:
    __slots__ = ('identifier', 'r', 'g', 'b', 'i', 'width', 'height')

    def __init__(self, red, green, blue, width, height, identifier=None):
        # type: (List[int], List[int], List[int], int, int, Any) -> None
        self.r = red
        self.g = green
        self.b = blue
        self.i = [int(sum(pixel) / 3) for pixel in zip(red, green, blue)]
        self.width = width
        self.height = height
        self.identifier = identifier

    def to_c_sequence(self):
        array_type = c_int * len(self.r)
        return Sequence(c_int_p(array_type(*self.r)),
                        c_int_p(array_type(*self.g)),
                        c_int_p(array_type(*self.b)),
                        c_int_p(array_type(*self.i)),
                        0.0, -1)
