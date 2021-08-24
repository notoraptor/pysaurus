import base64
from typing import Any, Optional, Tuple, Union

from pysaurus.core.classes import AbstractMatrix
from pysaurus.core.fraction import Fraction
from pysaurus.core.modules import ImageUtils

Bytes = Union[bytes, bytearray]


class GroupSignature:
    __slots__ = "r", "m", "n"

    def __init__(self, pixel_distance_radius: int, group_min_size: int, nb_groups: int):
        self.r = pixel_distance_radius
        self.m = group_min_size
        self.n = nb_groups

    def to_dict(self):
        return self.r, self.m, self.n

    @classmethod
    def from_dict(cls, d):
        return cls(*d)


class Miniature(AbstractMatrix):
    __slots__ = ("identifier", "r", "g", "b", "i", "group_signature")

    def __init__(
        self, red, green, blue, width, height, identifier=None, group_signature=None
    ):
        # type: (Bytes, Bytes, Bytes, int, int, Any, GroupSignature) -> None
        super().__init__(width, height)
        self.r = red
        self.g = green
        self.b = blue
        self.i = None
        self.identifier = identifier
        self.group_signature = group_signature

    def has_group_signature(self, pixel_distance_radius: int, group_min_size: int):
        return (
            self.group_signature
            and self.group_signature.r == pixel_distance_radius
            and self.group_signature.m == group_min_size
        )

    def set_group_signature(
        self, pixel_distance_radius, group_min_size: int, nb_groups: int
    ):
        self.group_signature = GroupSignature(
            pixel_distance_radius, group_min_size, nb_groups
        )

    @property
    def size(self):
        return self.width * self.height

    @property
    def nb_pixels(self):
        return len(self.r)

    def data(self):
        for i in range(len(self.r)):
            yield self.r[i], self.g[i], self.b[i]

    def to_dict(self):
        return {
            "r": base64.b64encode(self.r).decode(),
            "g": base64.b64encode(self.g).decode(),
            "b": base64.b64encode(self.b).decode(),
            "w": self.width,
            "h": self.height,
            "i": self.identifier,
            "s": self.group_signature.to_dict() if self.group_signature else None,
        }

    def global_intensity(self) -> Fraction:
        return Fraction(sum(self.r) + sum(self.g) + sum(self.b), 3 * self.size)

    @staticmethod
    def from_dict(dct: dict):
        gs = dct.get("s", None)
        return Miniature(
            red=base64.b64decode(dct["r"]),
            green=base64.b64decode(dct["g"]),
            blue=base64.b64decode(dct["b"]),
            width=dct["w"],
            height=dct["h"],
            identifier=dct["i"],
            group_signature=(gs if gs is None else GroupSignature.from_dict(gs)),
        )

    @staticmethod
    def from_file_name(file_name, dimensions, identifier=None):
        # type: (str, Tuple[int, int], Optional[Any]) -> Miniature
        image = ImageUtils.open_rgb_image(file_name)
        thumbnail = image.resize(dimensions)
        width, height = dimensions
        size = width * height
        red = bytearray(size)
        green = bytearray(size)
        blue = bytearray(size)
        for i, (r, g, b) in enumerate(thumbnail.getdata()):
            red[i] = r
            green[i] = g
            blue[i] = b
        return Miniature(red, green, blue, width, height, identifier)
