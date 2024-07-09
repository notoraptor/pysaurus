import base64
import os
import platform
import sys
from html.parser import HTMLParser
from io import BytesIO
from typing import Any, Iterator, Sequence, Tuple

from PIL import Image

from pysaurus.core import core_exceptions
from pysaurus.core.constants import THUMBNAIL_EXTENSION

ImagePosition = Tuple[Any, int, int]


class HTMLStripper(HTMLParser):
    """HTML parser class to remove HTML tags from a string.
    Example:
        text = HTMLStripper.strip(text)
    Reference: (2018/09/24) https://stackoverflow.com/a/925630
    """

    def error(self, message):
        pass

    def __init__(self):
        """Constructor"""
        super(HTMLStripper, self).__init__(convert_charrefs=True)
        self.fed = []

    def handle_data(self, data):
        """Split text to blank delimiters and store text pieces."""
        self.fed.extend(data.split())

    def get_data(self):
        """Return filtered text pieces, joined with space.
        Each spaces sequence should contain only 1 space in returned text.
        """
        return " ".join(self.fed)

    @staticmethod
    def clean(title: str) -> str:
        """
        Remove HTML tags, simple and double starting/ending quotes from given string.
        :param title: text to clear
        :return: cleared text
        TODO Unused (video meta titles never cleaned?)
        """
        if title:
            html_stripper = HTMLStripper()
            html_stripper.feed(title)
            title = html_stripper.get_data()
            strip_again = True
            while strip_again:
                strip_again = False
                for character in ('"', "'"):
                    if title.startswith(character) and title.endswith(character):
                        title = title.strip(character)
                        strip_again = True
        return title


class System:
    @staticmethod
    def is_windows():
        return sys.platform == "win32"

    @staticmethod
    def is_linux():
        return sys.platform == "linux"

    @staticmethod
    def is_mac():
        return sys.platform == "darwin"

    @staticmethod
    def platform():
        return sys.platform

    @staticmethod
    def is_case_insensitive(folder="."):
        base_name = os.path.join(folder, "tmp")
        count = 0
        while True:
            test_name = f"{base_name}{count}"
            if FileSystem.path.exists(test_name):
                count += 1
            else:
                break
        with open(test_name, "w+"):
            is_insensitive = FileSystem.path.exists(test_name.upper())
        FileSystem.unlink(test_name)
        return is_insensitive

    @staticmethod
    def get_identifier():
        bits_info = platform.architecture()[0]
        if bits_info == "32bit":
            bits = 32
        elif bits_info == "64bit":
            bits = 64
        else:
            raise core_exceptions.UnsupportedSystemError(System.platform(), bits_info)
        if System.is_windows():
            name = "win"
        elif System.is_linux():
            name = "lin"
        elif System.is_mac():
            name = "mac"
        else:
            raise core_exceptions.UnsupportedSystemError(System.platform())
        return f"{name}{bits}"

    @staticmethod
    def get_lib_basename(name, prefix="lib"):
        if System.is_windows():
            return f"{name}.dll"
        elif System.is_linux():
            return f"{prefix}{name}.so"
        else:
            raise core_exceptions.UnsupportedSystemError(System.platform())

    @staticmethod
    def get_exe_basename(name):
        return f"{name}.exe" if System.is_windows() else name


class ImageUtils:
    IMAGE_RGB_MODE = "RGB"
    IMAGE_GRAY_MODE = "L"
    THUMBNAIL_DIMENSION = 32
    THUMBNAIL_SIZE = (THUMBNAIL_DIMENSION, THUMBNAIL_DIMENSION)

    @staticmethod
    def __save_image(mode, size, data, name):
        output_image = Image.new(mode=mode, size=size, color=0)
        output_image.putdata(data)
        output_image.save(name)
        return output_image

    @staticmethod
    def open_rgb_image(file_name) -> Image:
        image = Image.open(file_name)
        if image.mode != ImageUtils.IMAGE_RGB_MODE:
            image = image.convert(ImageUtils.IMAGE_RGB_MODE)
        return image

    @staticmethod
    def from_blob(binary_data) -> Image:
        blob = BytesIO(binary_data)
        return ImageUtils.open_rgb_image(blob)

    @staticmethod
    def save_gray_image(width, height, data, name):
        # Data must be a list of gray values in [0; 255].
        return ImageUtils.__save_image(
            ImageUtils.IMAGE_GRAY_MODE, (width, height), data, name
        )

    @staticmethod
    def save_rgb_image(width, height, data, name):
        # Data must be a list of triples (r, g, b), each in [0; 255].
        return ImageUtils.__save_image(
            ImageUtils.IMAGE_RGB_MODE, (width, height), data, name
        )

    @staticmethod
    def new_rgb_image(data, width, height):
        image = Image.new("RGB", (width, height))
        image.putdata(data)
        return image

    @staticmethod
    def new_rgb_surface(width: int, height: int, r: int, g: int, b: int):
        image = Image.new("RGB", (width, height))
        image.putdata([(r, g, b)] * (width * height))
        return image

    @staticmethod
    def thumbnail_to_base64(thumb_path: str):
        if not FileSystem.path.isfile(thumb_path):
            return None
        image = ImageUtils.open_rgb_image(thumb_path)
        buffered = BytesIO()
        image.save(buffered, format=THUMBNAIL_EXTENSION)
        image_string = base64.b64encode(buffered.getvalue())
        return image_string

    @staticmethod
    def get_near_front_pixels(
        width: int, height: int
    ) -> Iterator[Tuple[ImagePosition, Sequence[ImagePosition]]]:
        # x, y:

        # 0, 0
        yield (0, 0), ((0, 0), (1, 0), (0, 1), (1, 1))
        # width - 1, 0
        yield (
            (width - 1, 0),
            ((width - 2, 0), (width - 1, 0), (width - 2, 1), (width - 1, 1)),
        )
        # 0, height - 1
        yield (
            (0, height - 1),
            ((0, height - 1), (1, height - 1), (0, height - 2), (1, height - 2)),
        )
        # width - 1, height - 1
        yield (
            (width - 1, height - 1),
            (
                (width - 2, height - 1),
                (width - 1, height - 1),
                (width - 2, height - 2),
                (width - 1, height - 2),
            ),
        )

        for x in range(1, width - 1):
            # x, 0
            yield (
                (x, 0),
                ((x - 1, 0), (x, 0), (x + 1, 0), (x - 1, 1), (x, 1), (x + 1, 1)),
            )
            # x, height - 1
            yield (
                (x, height - 1),
                (
                    (x - 1, height - 1),
                    (x, height - 1),
                    (x + 1, height - 1),
                    (x - 1, height - 2),
                    (x, height - 2),
                    (x + 1, height - 2),
                ),
            )
        for y in range(1, height - 1):
            # 0, y
            yield (
                (0, y),
                ((0, y - 1), (1, y - 1), (0, y), (1, y), (0, y + 1), (1, y + 1)),
            )
            # width - 1, y
            yield (
                (width - 1, y),
                (
                    (width - 2, y - 1),
                    (width - 1, y - 1),
                    (width - 2, y),
                    (width - 1, y),
                    (width - 2, y + 1),
                    (width - 1, y + 1),
                ),
            )
        # x in [1; width - 2], y in [1; height - 2]
        remaining_size = (width - 2) * (height - 2)
        for index in range(0, remaining_size):
            x = index % (width - 2) + 1
            y = index // (width - 2) + 1
            yield (
                (x, y),
                (
                    (x - 1, y - 1),
                    (x, y - 1),
                    (x + 1, y - 1),
                    (x - 1, y),
                    (x, y),
                    (x + 1, y),
                    (x - 1, y + 1),
                    (x, y + 1),
                    (x + 1, y + 1),
                ),
            )


class FNV64:
    FNV_64_PRIME = 0x00000100000001B3
    FNV_64_OFFSET_BASIS = 0xCBF29CE484222325

    @staticmethod
    def _bytes_to_uint64(data):
        h = FNV64.FNV_64_OFFSET_BASIS
        for byte in data:
            h *= FNV64.FNV_64_PRIME
            h &= 0xFFFFFFFFFFFFFFFF
            h ^= byte
        return h

    @staticmethod
    def hash(string):
        # type: (str) -> str
        h = FNV64._bytes_to_uint64(string.encode())
        return hex(h)[2:]


class _FileSystemPath:
    @classmethod
    def exists(cls, path: str):
        return os.path.exists(path)

    @classmethod
    def isfile(cls, path: str):
        return os.path.isfile(path)

    @classmethod
    def isdir(cls, path: str):
        return os.path.isdir(path)

    @classmethod
    def getmtime(cls, path: str):
        return os.path.getmtime(path)

    @classmethod
    def getsize(cls, path: str):
        return os.path.getsize(path)


class _FileSystem:
    path = _FileSystemPath
    DirEntry = os.DirEntry

    @classmethod
    def scandir(cls, path: str):
        return os.scandir(path)

    @classmethod
    def stat(cls, path: str):
        return os.stat(path)

    @classmethod
    def utime(cls, path: str, times: tuple):
        return os.utime(path, times)

    @classmethod
    def listdir(cls, path: str):
        return os.listdir(path)

    @classmethod
    def walk(cls, path: str):
        return os.walk(path)

    @classmethod
    def makedirs(cls, *args, **kwargs):
        return os.makedirs(*args, **kwargs)

    @classmethod
    def unlink(cls, path: str):
        return os.unlink(path)

    @classmethod
    def rename(cls, old_path: str, new_path: str):
        return os.rename(old_path, new_path)

    @classmethod
    def startfile(cls, path: str):
        return os.startfile(path)


# May be used for debugging, e.g. to trace os file/folder operations.
FileSystem = _FileSystem
