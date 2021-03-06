import base64
import os
import sys
import tempfile
import tkinter as tk
from html.parser import HTMLParser
from typing import Tuple

import ujson as json
from PIL import Image, ImageTk
from moviepy.video.io.VideoFileClip import VideoFileClip

from pysaurus.core.exceptions import NoVideoClip


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
            test_name = "%s%d" % (base_name, count)
            if FileSystem.path.exists(test_name):
                count += 1
            else:
                break
        with open(test_name, "w+"):
            is_insensitive = FileSystem.path.exists(test_name.upper())
        FileSystem.unlink(test_name)
        return is_insensitive


class VideoClipping:
    @staticmethod
    def get_video_duration(path):
        return VideoFileClip(path).duration

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
            raise NoVideoClip()
        if unique_id is None:
            path = os.path.abspath(path)
            unique_id = FNV64.hash(path)
        output_name = "%s_%s_%s.mp4" % (unique_id, time_start, clip_seconds)
        print("Clip from %s to %s sec in: %s" % (time_start, time_end, output_name))
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


class Color:
    HEX_DIGITS = "0123456789ABCDEF"

    @classmethod
    def _unit_to_hex(cls, value):
        return cls.HEX_DIGITS[value // 16] + cls.HEX_DIGITS[value % 16]

    @classmethod
    def rgb_to_hex(cls, color: Tuple[int, int, int]):
        return "".join(
            cls._unit_to_hex(value)
            for value in (color if isinstance(color, tuple) else (color,))
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


class Workspace:
    directory = tempfile.gettempdir()
    prefix = tempfile.gettempprefix()

    @classmethod
    def new_path(cls):
        from pysaurus.core.components import FilePath

        extension = "json"
        temp_file_id = 0
        while True:
            temp_file_path = FilePath(
                cls.directory, "%s%s" % (cls.prefix, temp_file_id), extension
            )
            if temp_file_path.exists():
                temp_file_id += 1
            else:
                break
        return temp_file_path

    @classmethod
    def save(cls, data):
        path = cls.new_path()
        with open(path.path, "w") as output_file:
            json.dump(data, output_file)
        return path

    @classmethod
    def load(cls, path):
        with open(str(path), "r") as input_file:
            return json.load(input_file)


class Display:
    @staticmethod
    def from_path(path):
        root = tk.Tk()
        img = Image.open(path)
        tk_image = ImageTk.PhotoImage(img)
        label = tk.Label(master=root)
        label["image"] = tk_image
        label.pack(side="left")
        root.mainloop()

    @staticmethod
    def from_images(*images):
        root = tk.Tk()
        tk_images = []
        for img in images:
            tk_image = ImageTk.PhotoImage(img)
            tk_images.append(tk_image)
            tk.Label(master=root, image=tk_image).pack(side="left")
        root.mainloop()


class TreeUtils:
    @staticmethod
    def collect_full_paths(tree: dict, collection: list, prefix=()):
        if not isinstance(prefix, list):
            prefix = list(prefix)
        if tree:
            for key, value in tree.items():
                TreeUtils.collect_full_paths(value, collection, prefix + [key])
        elif prefix:
            collection.append(prefix)

    @staticmethod
    def check_source_path(dct, seq, index=0):
        if index < len(seq):
            TreeUtils.check_source_path(dct[seq[index]], seq, index + 1)

    @staticmethod
    def get_source_from_dict(inp, seq, index=0):
        if index < len(seq):
            return TreeUtils.get_source_from_dict(inp[seq[index]], seq, index + 1)
        else:
            return inp


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
