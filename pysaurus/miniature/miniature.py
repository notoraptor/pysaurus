import base64
from io import BytesIO
from typing import Any, Optional, Tuple, Union

import numpy as np

from pysaurus.core.classes import AbstractMatrix
from pysaurus.core.fraction import Fraction
from pysaurus.core.modules import ImageUtils

Bytes = Union[bytes, bytearray]


class NumpyMiniature:
    __slots__ = "r", "g", "b", "width", "height", "identifier"

    def __init__(
        self, r: Bytes, g: Bytes, b: Bytes, width: int, height: int, identifier
    ):
        self.width = width
        self.height = height
        self.r = np.asarray(r, dtype=np.float32).reshape((height, width))
        self.g = np.asarray(g, dtype=np.float32).reshape((height, width))
        self.b = np.asarray(b, dtype=np.float32).reshape((height, width))
        self.identifier = identifier

    @classmethod
    def from_image(cls, thumbnail, identifier=None):
        width, height = thumbnail.size
        size = width * height
        red = bytearray(size)
        green = bytearray(size)
        blue = bytearray(size)
        for i, (r, g, b) in enumerate(thumbnail.getdata()):
            red[i] = r
            green[i] = g
            blue[i] = b
        return cls(red, green, blue, width, height, identifier)


class Miniature(AbstractMatrix):
    __slots__ = ("identifier", "r", "g", "b", "i", "video_id")

    def __init__(self, red, green, blue, width, height, identifier=None):
        # type: (Bytes, Bytes, Bytes, int, int, Any) -> None
        super().__init__(width, height)
        self.r = red
        self.g = green
        self.b = blue
        self.i = None
        self.identifier = identifier
        self.video_id = None

    size = property(lambda self: self.width * self.height)
    nb_pixels = property(lambda self: len(self.r))

    def to_numpy(self) -> NumpyMiniature:
        return NumpyMiniature(
            bytearray(self.r),
            bytearray(self.g),
            bytearray(self.b),
            self.width,
            self.height,
            self.identifier,
        )

    def data(self):
        for i in range(len(self.r)):
            yield self.r[i], self.g[i], self.b[i]

    def global_intensity(self) -> Fraction:
        return Fraction(sum(self.r) + sum(self.g) + sum(self.b), 3 * self.size)

    def to_dict(self):
        return {
            "r": base64.b64encode(self.r).decode(),
            "g": base64.b64encode(self.g).decode(),
            "b": base64.b64encode(self.b).decode(),
            "w": self.width,
            "h": self.height,
            "i": self.identifier,
        }

    @staticmethod
    def from_dict(dct: dict):
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
        return Miniature._img_to_mnt(image, dimensions, identifier)

    @staticmethod
    def from_file_data(binary_data, dimensions, identifier=None):
        # type: (bytes, Tuple[int, int], Optional[Any]) -> Miniature
        blob = BytesIO(binary_data)
        image = ImageUtils.open_rgb_image(blob)
        return Miniature._img_to_mnt(image, dimensions, identifier)

    @staticmethod
    def _img_to_mnt(image, dimensions: Tuple[int, int], identifier: Optional[Any]):
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

    @staticmethod
    def from_image(thumbnail, identifier: Optional[Any] = None):
        width, height = thumbnail.size
        r, g, b = thumbnail.split()
        return Miniature(
            r.tobytes(), g.tobytes(), b.tobytes(), width, height, identifier
        )
