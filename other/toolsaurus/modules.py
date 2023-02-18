import tkinter as tk
from typing import Iterable, Tuple

from PIL import Image, ImageTk

from pysaurus.core import functions
from pysaurus.database.viewport.view_tools import SearchDef
from pysaurus.video.video import Video
from pysaurus.video.video_features import VideoFeatures


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


class OtherVideoFeatures(VideoFeatures):
    @staticmethod
    def find(search: SearchDef, videos: Iterable[Video]) -> Iterable[Video]:
        terms = functions.string_to_pieces(search.text)
        video_filter = getattr(VideoFeatures, f"has_terms_{search.cond}")
        return (video for video in videos if video_filter(video, terms))
