import io
import os
import pathlib

import pytest

from pysaurus.core.modules import ImageUtils
from videre import Picture
from videre.windowing.windowfactory import WindowLD


class SrcProvider:
    _string = os.path.join(os.path.dirname(__file__), "flowers-7660120_640.jpg")
    _path = pathlib.Path(_string)

    def string(self):
        return self._string

    def path(self):
        return self._path

    def bytes(self) -> bytes:
        output = io.BytesIO()
        image = ImageUtils.open_rgb_image(self._string)
        image.save(output, format=image.format)
        return output.getvalue()

    def bytearray(self):
        return bytearray(self.bytes())

    def file_like(self):
        return io.BytesIO(self.bytes())


@pytest.mark.parametrize("src", ["string", "path", "bytes", "bytearray", "file_like"])
def test_image(src, image_testing):
    src_provider = SrcProvider()
    with WindowLD() as window:
        window.controls = [Picture(src=getattr(src_provider, src)())]
        image_testing(window.snapshot())


@pytest.mark.parametrize("alt", [None, "Bad image!"])
def test_bad_image(alt, image_testing):
    with WindowLD() as window:
        window.controls = [Picture("", alt=alt)]
        image_testing(window.snapshot())
