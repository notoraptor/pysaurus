from typing import Callable, Optional, Union

import pygame
import pygame.gfxdraw

from videre.colors import ColorDef, Colors, parse_color
from videre.core.pygame_utils import PygameUtils


class Gradient(PygameUtils):
    """
    Inspired from (2024/06/30): https://stackoverflow.com/a/62336993
    """

    __slots__ = ("_colors", "_vertical", "_base", "_gen")

    def __init__(self, *colors: pygame.Color, vertical=False):
        super().__init__()

        self._colors = colors or [Colors.transparent]
        self._vertical: bool = vertical
        self._base: Optional[pygame.Surface] = None
        self._gen: Callable[[int, int], pygame.Surface] = (
            self._plain if len(self._colors) == 1 else self._gradient
        )

    def _plain(self, width: int, height: int) -> pygame.Surface:
        surface = self._new_surface(width, height)
        surface.fill(self._colors[0])
        return surface

    def _gradient(self, width: int, height: int) -> pygame.Surface:
        return pygame.transform.smoothscale(self._get_base(), (width, height))

    def _get_base(self) -> pygame.Surface:
        if self._base is None:
            if self._vertical:
                w = 2
                h = len(self._colors)
            else:
                w = len(self._colors)
                h = 2
            base = self._new_surface(w, h)
            for i, color in enumerate(self._colors):
                if self._vertical:
                    x1, x2 = 0, 1
                    y1 = y2 = i
                else:
                    x1 = x2 = i
                    y1, y2 = 0, 1
                pygame.gfxdraw.line(base, x1, y1, x2, y2, color)
            self._base = base

        return self._base

    def generate(self, width: int, height: int) -> pygame.Surface:
        return self._gen(width, height)

    @classmethod
    def parse(cls, coloring: Union[ColorDef, "Gradient"]) -> "Gradient":
        if isinstance(coloring, Gradient):
            return coloring
        return Gradient(parse_color(coloring))


ColoringDefinition = Union[ColorDef, Gradient]
