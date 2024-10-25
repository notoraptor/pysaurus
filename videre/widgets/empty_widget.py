import pygame

from videre.widgets.widget import Widget


class EmptyWidget(Widget):
    __wprops__ = {}
    __slots__ = ()

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        return self._new_surface(0, 0)
