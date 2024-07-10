import pygame

from videre.layouts.abstractlayout import AbstractLayout
from videre.widgets.widget import Widget


class Zone(AbstractLayout):
    __wprops__ = {"width", "height"}
    __size__ = 1
    __slots__ = ()

    def __init__(self, control: Widget, width: int, height: int, x=0, y=0, **kwargs):
        super().__init__([control], **kwargs)
        self._set_wprop("width", width)
        self._set_wprop("height", height)
        self.x = x
        self.y = y

    @property
    def width(self) -> int:
        return self._get_wprop("width")

    @property
    def height(self) -> int:
        return self._get_wprop("height")

    @property
    def control(self) -> Widget:
        return self._controls()[0]

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        if width is None:
            width = self.width
        else:
            width = min(width, self.width)
        if height is None:
            height = self.height
        else:
            height = min(height, self.height)
        return self.control.render(window, width, height)
