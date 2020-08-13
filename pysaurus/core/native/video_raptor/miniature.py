import base64
from typing import Any, Optional, Tuple

from pysaurus.core.modules import ImageUtils


class Miniature:
    __slots__ = ('identifier', 'r', 'g', 'b', 'i', 'width', 'height')

    def __init__(self, red, green, blue, width, height, identifier=None):
        # type: (bytearray, bytearray, bytearray, int, int, Any) -> None
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

    def coordinates_around(self, x, y, radius=1):
        coordinates = []
        for local_x in range(max(0, x - radius), min(x + radius, self.width - 1) + 1):
            for local_y in range(max(0, y - radius), min(y + radius, self.height - 1) + 1):
                coordinates.append((local_x, local_y))
        return coordinates

    def tuples(self):
        for i in range(len(self.r)):
            yield (self.r[i], self.g[i], self.b[i])

    def to_dict(self):
        return {
            'r': base64.b64encode(self.r).decode(),
            'g': base64.b64encode(self.g).decode(),
            'b': base64.b64encode(self.b).decode(),
            'w': self.width,
            'h': self.height,
            'i': self.identifier,
        }

    @staticmethod
    def from_dict(dct):
        return Miniature(red=base64.b64decode(dct['r']),
                         green=base64.b64decode(dct['g']),
                         blue=base64.b64decode(dct['b']),
                         width=dct['w'],
                         height=dct['h'],
                         identifier=dct['i'])

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
