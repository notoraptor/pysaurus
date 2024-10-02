import pygame

from videre.layouts.abstractlayout import AbstractLayout
from videre.widgets.widget import Widget


class View(AbstractLayout):
    __wprops__ = {"width", "height"}
    __size__ = 1
    __slots__ = ()

    def __init__(self, control: Widget, width: int, height: int, **kwargs):
        super().__init__([control], **kwargs)
        self._set_wprops(width=width, height=height)

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
    def control(self) -> Widget:
        return self._controls()[0]

    @control.setter
    def control(self, control: Widget):
        self._set_controls((control,))

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
