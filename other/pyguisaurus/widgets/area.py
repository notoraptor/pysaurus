from typing import Sequence, Union

import pygame
import pygame.gfxdraw

from other.pyguisaurus.colors import Gradient
from other.pyguisaurus.widgets.widget import Widget


class Area(Widget):
    __attributes__ = {"width", "height", "coloring"}
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
        self._set_attribute("width", width)
        self._set_attribute("height", height)
        self._set_attribute("coloring", coloring)
        self.x = x
        self.y = y

    @property
    def width(self) -> int:
        return self._get_attribute("width")

    @property
    def height(self) -> int:
        return self._get_attribute("height")

    @property
    def coloring(self) -> Gradient:
        return self._get_attribute("coloring")

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        return self.coloring.generate(self.width, self.height)
