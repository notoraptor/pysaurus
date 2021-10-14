import base64
import os
import platform
import sys
from html.parser import HTMLParser
from io import BytesIO

from PIL import Image
from moviepy.video.io.VideoFileClip import VideoFileClip

from pysaurus.core import core_exceptions
from pysaurus.core.constants import THUMBNAIL_EXTENSION


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

    @classmethod
    def strip(cls, msg):
        """Remove HTML tags from given message and return stripped message."""
        html_stripper = HTMLStripper()
        html_stripper.feed(msg)
        return html_stripper.get_data()


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
        if System.is_windows():
            return f"{name}.exe"
        return name


class VideoClipping:
    @staticmethod
    def video_clip(path, time_start=0, clip_seconds=10, unique_id=None):
        assert isinstance(time_start, int) and time_start >= 0
        assert isinstance(clip_seconds, int) and clip_seconds > 0
        clip = VideoFileClip(path)
        time_end = time_start + clip_seconds
        if time_start > clip.duration:
            time_start = clip.duration
        if time_end > clip.duration:
            time_end = clip.duration
        if time_start - time_end == 0:
            raise core_exceptions.ZeroLengthError()
        if unique_id is None:
            path = os.path.abspath(path)
            unique_id = FNV64.hash(path)
        output_name = f"{unique_id}_{time_start}_{clip_seconds}.mp4"
        print("Clip from", time_start, "to", time_end, "sec in:", output_name)
        sub_clip = clip.subclip(time_start, time_end)
        sub_clip.write_videofile(output_name)
        sub_clip.close()
        clip.close()
        del clip
        del sub_clip
        return output_name

    @staticmethod
    def video_clip_to_base64(path, time_start=0, clip_seconds=10, unique_id=None):
        output_path = VideoClipping.video_clip(
            path, time_start, clip_seconds, unique_id
        )
        with open(output_path, "rb") as file:
            content = file.read()
        encoded = base64.b64encode(content)
        print(len(encoded) / len(content))
        FileSystem.unlink(output_path)
        return encoded


class ImageUtils:
    IMAGE_RGB_MODE = "RGB"
    IMAGE_GRAY_MODE = "L"
    DEFAULT_THUMBNAIL_SIZE = (32, 32)

    @staticmethod
    def __save_image(mode, size, data, name):
        output_image = Image.new(mode=mode, size=size, color=0)
        output_image.putdata(data)
        output_image.save(name)
        return output_image

    @staticmethod
    def open_rgb_image(file_name):
        image = Image.open(file_name)
        if image.mode != ImageUtils.IMAGE_RGB_MODE:
            image = image.convert(ImageUtils.IMAGE_RGB_MODE)
        return image

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
    def thumbnail_to_base64(thumb_path: str):
        if not FileSystem.path.isfile(thumb_path):
            return None
        image = ImageUtils.open_rgb_image(thumb_path)
        buffered = BytesIO()
        image.save(buffered, format=THUMBNAIL_EXTENSION)
        image_string = base64.b64encode(buffered.getvalue())
        return image_string


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


def _silent(*args, **kwargs):
    pass


# _print = print
_print = _silent


class _FileSystemPath:
    @classmethod
    def exists(cls, path: str):
        _print("FILESYSTEM PATH EXISTS", path)
        return os.path.exists(path)

    @classmethod
    def isfile(cls, path: str):
        _print("FILESYSTEM PATH.ISFILE", path)
        return os.path.isfile(path)

    @classmethod
    def isdir(cls, path: str):
        _print("FILESYSTEM PATH ISDIR", path)
        return os.path.isdir(path)

    @classmethod
    def getmtime(cls, path: str):
        _print("FILESYSTEM PATH GETMTIME")
        return os.path.getmtime(path)

    @classmethod
    def getsize(cls, path: str):
        _print("FILESYSTEM PATH GETSIZE")
        return os.path.getsize(path)


class _FileSystem:
    path = _FileSystemPath

    @classmethod
    def scandir(cls, path: str):
        _print("FILESYSTEM SCANDIR")
        return os.scandir(path)

    @classmethod
    def stat(cls, path: str):
        _print("FILESYSTEM STAT")
        return os.stat(path)

    @classmethod
    def utime(cls, path: str, times: tuple):
        _print("FILESYSTEM UTIME")
        return os.utime(path, times)

    @classmethod
    def listdir(cls, path: str):
        _print("FILESYSTEM LISTDIR")
        return os.listdir(path)

    @classmethod
    def walk(cls, path: str):
        _print("FILESYSTEM WALK")
        return os.walk(path)

    @classmethod
    def makedirs(cls, *args, **kwargs):
        _print("FILESYSTEM MAKEDIRS", *args, kwargs)
        return os.makedirs(*args, **kwargs)

    @classmethod
    def unlink(cls, path: str):
        _print("FILESYSTEM UNLINK", path)
        return os.unlink(path)

    @classmethod
    def rename(cls, old_path: str, new_path: str):
        _print("FILESYSTEM RENAME")
        return os.rename(old_path, new_path)

    @classmethod
    def startfile(cls, path: str):
        _print("FILESYSTEM STARTFILE")
        return os.startfile(path)


FileSystem = _FileSystem
