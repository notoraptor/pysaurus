import pygame

from videre.layouts.abstractlayout import AbstractLayout
from videre.widgets.widget import Widget


class View(AbstractLayout):
    __wprops__ = {"width", "height"}
    __size__ = 1
    __slots__ = ()

    def __init__(
        self, control: Widget, width: int = None, height: int = None, **kwargs
    ):
        super().__init__([control], **kwargs)
        self._set_wprops(width=width, height=height)

    @property
    def width(self) -> int | None:
        return self._get_wprop("width")

    @width.setter
    def width(self, width: int | None):
        self._set_wprop("width", width)

    @property
    def height(self) -> int | None:
        return self._get_wprop("height")

    @height.setter
    def height(self, height: int | None):
        self._set_wprop("height", height)

    @property
    def control(self) -> Widget:
        return self._controls()[0]

    @control.setter
    def control(self, control: Widget):
        self._set_controls((control,))

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        width = _resolve_size(self.width, width)
        height = _resolve_size(self.height, height)
        surface = self.control.render(window, width, height)
        if width is None and height is None:
            return surface
        if width is None:
            width = surface.get_width()
        if height is None:
            height = surface.get_height()
        if width == surface.get_width() and height == surface.get_height():
            return surface
        crop = self._new_surface(width, height)
        crop.blit(surface, (0, 0))
        return crop


def _resolve_size(view_size: int | None, parent_size: int | None) -> int | None:
    if view_size is None and parent_size is None:
        return None
    elif view_size is None:
        return parent_size
    elif parent_size is None:
        return view_size
    else:
        return min(view_size, parent_size)
