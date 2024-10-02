from typing import Sequence, Union

import pygame
import pygame.gfxdraw

from videre import Gradient
from videre.widgets.widget import Widget


class Rectangle(Widget):
    __wprops__ = {"width", "height", "coloring"}
    __slots__ = ()

    def __init__(
        self,
        width: int,
        height: int,
        coloring: Union[Gradient, pygame.Color, Sequence[pygame.Color]],
        x=0,
        y=0,
        **kwargs
    ):
        if isinstance(coloring, pygame.Color):
            coloring = [coloring]
        if not isinstance(coloring, Gradient):
            coloring = Gradient(*coloring)

        super().__init__(**kwargs)
        self._set_wprops(width=width, height=height, coloring=coloring)
        self.x = x
        self.y = y

    @property
    def width(self) -> int:
        return self._get_wprop("width")

    @width.setter
    def width(self, width: int):
        self._set_wprop("width", width)

    @property
    def height(self) -> int:
        return self._get_wprop("height")

    @height.setter
    def height(self, height: int):
        self._set_wprop("height", height)

    @property
    def coloring(self) -> Gradient:
        return self._get_wprop("coloring")

    @coloring.setter
    def coloring(self, coloring: Union[Gradient, pygame.Color, Sequence[pygame.Color]]):
        if isinstance(coloring, pygame.Color):
            coloring = [coloring]
        if not isinstance(coloring, Gradient):
            coloring = Gradient(*coloring)
        self._set_wprop("coloring", coloring)

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        return self.coloring.generate(self.width, self.height)
