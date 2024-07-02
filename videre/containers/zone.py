import pygame

from videre.containers.container import Container
from videre.widgets.widget import Widget


class Zone(Container):
    __attributes__ = {"width", "height"}
    __size__ = 1
    __slots__ = ()

    def __init__(self, control: Widget, width: int, height: int, x=0, y=0, **kwargs):
        super().__init__([control], **kwargs)
        self._set_attribute("width", width)
        self._set_attribute("height", height)
        self.x = x
        self.y = y

    @property
    def width(self) -> int:
        return self._get_attribute("width")

    @property
    def height(self) -> int:
        return self._get_attribute("height")

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
