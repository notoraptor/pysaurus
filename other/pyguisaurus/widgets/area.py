import pygame

from other.pyguisaurus.widgets.widget import Widget


class Area(Widget):
    __attributes__ = {"width", "height", "color"}
    __slots__ = ()

    def __init__(
        self, width: int, height: int, color: pygame.Color, x=0, y=0, **kwargs
    ):
        super().__init__(**kwargs)
        self._set_attribute("width", width)
        self._set_attribute("height", height)
        self._set_attribute("color", color)
        self.x = x
        self.y = y

    @property
    def width(self) -> int:
        return self._get_attribute("width")

    @property
    def height(self) -> int:
        return self._get_attribute("height")

    @property
    def color(self) -> pygame.Color:
        return self._get_attribute("color")

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        surface = self._new_surface(self.width, self.height)
        surface.fill(self.color)
        return surface
