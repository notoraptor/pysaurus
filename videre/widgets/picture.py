import io
import logging
import sys
from pathlib import Path
from typing import BinaryIO, Union

import pygame

from videre.widgets.text import Text
from videre.widgets.widget import Widget

ImageSourceType = Union[str, Path, bytes, bytearray, BinaryIO]

logger = logging.getLogger(__name__)


class Picture(Widget):
    __wprops__ = {"alt", "src"}
    __slots__ = ()

    def __init__(self, src: ImageSourceType, alt="image", **kwargs):
        super().__init__(**kwargs)
        self.src = src
        self.alt = alt

    @property
    def src(self) -> ImageSourceType:
        return self._get_wprop("src")

    @src.setter
    def src(self, src: ImageSourceType):
        self._set_wprop("src", src)

    @property
    def alt(self) -> str:
        return self._get_wprop("alt")

    @alt.setter
    def alt(self, alt: str):
        self._set_wprop("alt", alt or "image")

    def _src_to_surface(self):
        src = self.src
        if isinstance(src, (bytes, bytearray)):
            src = io.BytesIO(src)
        try:
            return pygame.image.load(src).convert_alpha()
        except Exception as exc:
            print("Cannot load an image.")
            import traceback

            traceback.print_tb(exc.__traceback__)
            print(type(exc), exc, file=sys.stderr)
            return None

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        surface = self._src_to_surface()
        if surface is None:
            surface = Text(self.alt).render(window, width, height)
        return surface
