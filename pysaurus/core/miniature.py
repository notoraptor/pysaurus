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


class Matrix:
    def __init__(self, data: list, width: int, height: int):
        self.data = data
        self.width = width
        self.height = height

    @classmethod
    def standardize(cls, value: int, max_size: int, default: int):
        if value is None:
            value = default
        elif value < 0:
            value = max_size - value
        assert 0 <= value < max_size, (value, max_size)
        return value

    def get(self, row_from, row_end, row_step, col_from, col_end, col_step):
        row_from = self.standardize(row_from, self.height, 0)
        row_end = self.standardize(row_end, self.height + 1, self.height)
        row_step = self.standardize(row_step, self.height, 1)
        col_from = self.standardize(col_from, self.width, 0)
        col_end = self.standardize(col_end, self.width + 1, self.width)
        col_step = self.standardize(col_step, self.width, 1)
        return [
            self.data[functions.coord_to_flat(x, y, self.width)]
            for y in range(row_from, row_end, row_step)
            for x in range(col_from, col_end, col_step)
        ]


class Miniature:
    __slots__ = ("identifier", "r", "g", "b", "i", "width", "height")

    def __init__(self, red, green, blue, width, height, identifier=None):
        # type: (Bytes, Bytes, Bytes, int, int, Any) -> None
        self.r = red
        self.g = green
        self.b = blue
        self.i = None
        self.width = width
        self.height = height
        self.identifier = identifier

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

    def to_dict(self):
        return {
            "r": base64.b64encode(self.r).decode(),
            "g": base64.b64encode(self.g).decode(),
            "b": base64.b64encode(self.b).decode(),
            "w": self.width,
            "h": self.height,
            "i": self.identifier,
        }

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

    def to_matrix(self):
        return Matrix(list(self.data()), self.width, self.height)

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

    @staticmethod
    def from_dict(dct):
        return Miniature(
            red=base64.b64decode(dct["r"]),
            green=base64.b64decode(dct["g"]),
            blue=base64.b64decode(dct["b"]),
            width=dct["w"],
            height=dct["h"],
            identifier=dct["i"],
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
