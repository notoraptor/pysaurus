import base64
from typing import Any, Optional, Tuple, Union

from pysaurus.core import functions
from pysaurus.core.modules import ImageUtils

Bytes = Union[bytes, bytearray]


class CornerZones:
    __slots__ = "w", "h", "tl", "tr", "bl", "br"

    def __init__(self, width, height, *, tl, tr, bl, br):
        self.w = width
        self.h = height
        self.tl = tl
        self.tr = tr
        self.bl = bl
        self.br = br


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


class Miniature:
    __slots__ = ("identifier", "r", "g", "b", "i", "width", "height", "group_signature")

    def __init__(self, red, green, blue, width, height, identifier=None, group_signature=None):
        # type: (Bytes, Bytes, Bytes, int, int, Any, GroupSignature) -> None
        self.r = red
        self.g = green
        self.b = blue
        self.i = None
        self.width = width
        self.height = height
        self.identifier = identifier
        self.group_signature = group_signature

    def has_group_signature(self, pixel_distance_radius: int, group_min_size: int):
        return (
            self.group_signature
            and self.group_signature.r == pixel_distance_radius
            and self.group_signature.m == group_min_size
        )

    def set_group_signature(self, pixel_distance_radius, group_min_size: int, nb_groups: int):
        self.group_signature = GroupSignature(pixel_distance_radius, group_min_size, nb_groups)

    @property
    def size(self):
        return self.width * self.height

    @property
    def nb_pixels(self):
        return len(self.r)

    def __coordinates_around(self, x, y, radius=1):
        coordinates = []
        for local_x in range(max(0, x - radius), min(x + radius, self.width - 1) + 1):
            for local_y in range(
                max(0, y - radius), min(y + radius, self.height - 1) + 1
            ):
                coordinates.append((local_x, local_y))
        return coordinates

    def data(self):
        for i in range(len(self.r)):
            yield self.r[i], self.g[i], self.b[i]

    def get_corner_zones(self) -> CornerZones:
        z_tr = []
        z_tl = []
        z_br = []
        z_bl = []
        t = list(self.data())
        half_len = len(t) // 2
        width = self.width
        for y in range(0, self.height // 2):
            z_tl += t[(y * width) : (y * width + width // 2)]
            z_tr += t[(y * width + width // 2) : ((y + 1) * width)]
            z_bl += t[(half_len + y * width) : (half_len + y * width + width // 2)]
            z_br += t[
                (half_len + y * width + width // 2) : (half_len + (y + 1) * width)
            ]
        return CornerZones(
            width=self.width // 2,
            height=self.height // 2,
            tl=z_tl,
            tr=z_tr,
            bl=z_bl,
            br=z_br,
        )

    @staticmethod
    def from_matrix(data, width, height, identifier=None):
        channel_r = []
        channel_g = []
        channel_b = []
        for r, g, b in data:
            channel_r.append(r)
            channel_g.append(g)
            channel_b.append(b)
        assert len(channel_r) == width * height
        return Miniature(
            bytearray(channel_r),
            bytearray(channel_g),
            bytearray(channel_b),
            width,
            height,
            identifier,
        )

    def to_dict(self):
        return {
            "r": base64.b64encode(self.r).decode(),
            "g": base64.b64encode(self.g).decode(),
            "b": base64.b64encode(self.b).decode(),
            "w": self.width,
            "h": self.height,
            "i": self.identifier,
            "s": self.group_signature.to_dict() if self.group_signature else None
        }

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
            group_signature=(gs if gs is None else GroupSignature.from_dict(gs))
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
