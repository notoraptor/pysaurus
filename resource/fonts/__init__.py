"""
https://notofonts.github.io/
https://github.com/notofonts/notofonts.github.io

https://github.com/notofonts/noto-cjk
https://github.com/googlefonts/noto-emoji
https://www.babelstone.co.uk/Fonts/Han.html
"""
import os
from typing import Dict, List

from fontTools.ttLib import TTFont


def _file_path(base, *path_pieces) -> str:
    path = os.path.join(base, *path_pieces)
    assert os.path.isfile(path)
    return path


def _font_paths(folder: str) -> List[str]:
    return [_file_path(folder, name) for name in os.listdir(folder)]


FOLDER_FONT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
PATH_BABEL_STONE_HAN = _file_path(FOLDER_FONT, "other-ttf/BabelStoneHan.ttf")
PATH_SOURCE_HAN_SANS_JP = _file_path(FOLDER_FONT, "other-ttf/SourceHanSans-VF.ttf")
PATH_SOURCE_HAN_SANS_TTC = _file_path(FOLDER_FONT, "other-ttc/SourceHanSans-VF.ttf.ttc")

_FOLDER_SOURCE_SANS = os.path.join(FOLDER_FONT, "source-sans", "TTF")
PATH_SOURCE_SANS_REGULAR = _file_path(_FOLDER_SOURCE_SANS, "SourceSans3-Regular.ttf")
PATH_SOURCE_SANS_LIGHT = _file_path(_FOLDER_SOURCE_SANS, "SourceSans3-Light.ttf")

_FOLDER_NOTO = os.path.join(FOLDER_FONT, "noto", "unhinted", "TTF")
_FOLDER_NOTO_SERIF = os.path.join(FOLDER_FONT, "noto-serif", "unhinted", "TTF")
_FOLDER_NOTO_MONO = os.path.join(FOLDER_FONT, "noto-mono", "unhinted", "TTF")

_NOTO_FONTS = _font_paths(_FOLDER_NOTO)
_NOTO_SERIF_FONTS = _font_paths(_FOLDER_NOTO_SERIF)

PATH_NOTO_MONO = _file_path(_FOLDER_NOTO_MONO, "NotoSansMono-Regular.ttf")
PATH_NOTO_REGULAR = _file_path(_FOLDER_NOTO, "NotoSans-Regular.ttf")


class _FontInfo:
    __slots__ = ("name", "path")

    def __init__(self, path: str):
        with TTFont(path) as font:
            self.name = font["name"].getDebugName(4)
        self.path = path

    def __repr__(self):
        return f"({self.name})[{self.path}]"

    def to_dict(self):
        return {self.name: self.path}


FONT_BABEL_STONE = _FontInfo(PATH_BABEL_STONE_HAN)
FONT_NOTO_REGULAR = _FontInfo(PATH_NOTO_REGULAR)


def _get_fonts(paths: List[str]) -> Dict[str, str]:
    output = {}
    for path in paths:
        with TTFont(path) as font:
            output[font["name"].getDebugName(4)] = path
    assert len(output) == len(paths)
    return output


def _get_noto_fonts() -> Dict[str, str]:
    sans_fonts = _get_fonts(_NOTO_FONTS)
    serif_fonts = _get_fonts(_NOTO_SERIF_FONTS)
    fonts = {**sans_fonts, **serif_fonts}
    assert len(fonts) == len(sans_fonts) + len(serif_fonts)
    return fonts


def get_fonts() -> Dict[str, str]:
    noto_fonts = _get_noto_fonts()
    fonts = {**noto_fonts, **FONT_BABEL_STONE.to_dict()}
    assert len(fonts) == len(noto_fonts) + 1
    return fonts
