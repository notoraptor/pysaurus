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


def _validate_file(path: str) -> str:
    assert os.path.isfile(path)
    return path


FOLDER_FONT = os.path.abspath(os.path.join(os.path.dirname(__file__)))

_FOLDER_SOURCE_SANS = os.path.join(FOLDER_FONT, "source-sans", "TTF")

# https://github.com/notofonts/notofonts.github.io
FOLDER_NOTO = os.path.join(FOLDER_FONT, "noto", "unhinted", "TTF")
FOLDER_NOTO_SERIF = os.path.join(FOLDER_FONT, "noto-serif", "unhinted", "TTF")

NOTO_FONTS = [
    _validate_file(os.path.join(FOLDER_NOTO, name)) for name in os.listdir(FOLDER_NOTO)
]
NOTO_SERIF_FONTS = [
    _validate_file(os.path.join(FOLDER_NOTO_SERIF, name))
    for name in os.listdir(FOLDER_NOTO_SERIF)
]

PATH_NOTO_FANGSONG_VERTICAL = _validate_file(
    os.path.join(FOLDER_NOTO, "NotoFangsongKSSVertical-Regular.ttf")
)

PATH_SOURCE_SANS_REGULAR = _validate_file(
    os.path.join(_FOLDER_SOURCE_SANS, "SourceSans3-Regular.ttf")
)
PATH_SOURCE_SANS_LIGHT = _validate_file(
    os.path.join(_FOLDER_SOURCE_SANS, "SourceSans3-Light.ttf")
)

PATH_SOURCE_HAN_SANS_JP = _validate_file(
    os.path.join(FOLDER_FONT, "SourceHanSans-VF.ttf")
)
PATH_SOURCE_HAN_SANS_TTC = _validate_file(
    os.path.join(FOLDER_FONT, "SourceHanSans-VF.ttf.ttc")
)

PATH_BABEL_STONE_HAN = _validate_file(os.path.join(FOLDER_FONT, "BabelStoneHan.ttf"))


def _get_font(path: str) -> Dict[str, str]:
    return {TTFont(path)["name"].getDebugName(4): path}


def _get_fonts(paths: List[str]) -> Dict[str, str]:
    output = {TTFont(path)["name"].getDebugName(4): path for path in paths}
    assert len(output) == len(paths)
    return output


def get_noto_sans_fonts() -> Dict[str, str]:
    return _get_fonts(NOTO_FONTS)


def get_noto_serif_fonts() -> Dict[str, str]:
    return _get_fonts(NOTO_SERIF_FONTS)


def get_noto_fonts() -> Dict[str, str]:
    sans_fonts = get_noto_sans_fonts()
    serif_fonts = get_noto_serif_fonts()
    fonts = {**sans_fonts, **serif_fonts}
    assert len(fonts) == len(sans_fonts) + len(serif_fonts)
    return fonts


def get_fonts() -> Dict[str, str]:
    noto_fonts = get_noto_fonts()
    babel_font = _get_font(PATH_BABEL_STONE_HAN)
    fonts = {**noto_fonts, **babel_font}
    assert len(fonts) == len(noto_fonts) + len(babel_font)
    return fonts
