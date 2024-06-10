import os

import flet as ft

from other.supertk.constants import LOREM_IPSUM_UNICODE_3
from pysaurus import package_dir

_CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__))
_MONOSPACE_FONT = os.path.join(
    _CURRENT_FOLDER, "fonts", "Roboto_Mono", "RobotoMono-VariableFont_wght.ttf"
)
assert os.path.isfile(_MONOSPACE_FONT)

font_path_1 = os.path.abspath(
    os.path.join(
        package_dir(),
        "..",
        "resource",
        "fonts",
        "source-sans",
        "TTF",
        "SourceSans3-Light.ttf",
    )
)
assert os.path.isfile(font_path_1)


def run(page: ft.Page):
    page.window_center()

    page.fonts = {"Roboto Mono": _MONOSPACE_FONT, "Source Sans Light": font_path_1}
    page.title = "Test page"
    page.scroll = True
    page.add(ft.Text(LOREM_IPSUM_UNICODE_3, font_family="Source Sans Light"))


def main():
    ft.app(run, view=ft.AppView.FLET_APP)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    main()
