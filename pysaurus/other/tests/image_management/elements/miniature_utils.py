from pysaurus.core.miniature_tools.miniature import Miniature
from pysaurus.core.classes import AbstractMatrix


class Matrix(AbstractMatrix):
    __slots__ = "array",

    def __init__(self, array: list, width: int, height: int):
        super().__init__(width, height)
        self.array = array

    def data(self):
        return self.array


class CornerZones:
    __slots__ = "w", "h", "tl", "tr", "bl", "br"

    def __init__(self, width, height, *, tl, tr, bl, br):
        self.w = width
        self.h = height
        self.tl = Matrix(tl, width, height)
        self.tr = Matrix(tr, width, height)
        self.bl = Matrix(bl, width, height)
        self.br = Matrix(br, width, height)


def get_corner_zones(self: Miniature) -> CornerZones:
    z_tr = []
    z_tl = []
    z_br = []
    z_bl = []
    t = list(self.data())
    half_len = len(t) // 2
    width = self.width
    for y in range(0, self.height // 2):
        z_tl += t[(y * width): (y * width + width // 2)]
        z_tr += t[(y * width + width // 2): ((y + 1) * width)]
        z_bl += t[(half_len + y * width): (half_len + y * width + width // 2)]
        z_br += t[
                (half_len + y * width + width // 2): (half_len + (y + 1) * width)
                ]
    return CornerZones(
        width=self.width // 2,
        height=self.height // 2,
        tl=z_tl,
        tr=z_tr,
        bl=z_bl,
        br=z_br,
    )


def coordinates_around(self: Miniature, x, y, radius=1):
    coordinates = []
    for local_x in range(max(0, x - radius), min(x + radius, self.width - 1) + 1):
        for local_y in range(
            max(0, y - radius), min(y + radius, self.height - 1) + 1
        ):
            coordinates.append((local_x, local_y))
    return coordinates


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
