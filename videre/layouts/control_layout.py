import pygame

from videre.layouts.abstractlayout import AbstractLayout


class ControlLayout(AbstractLayout):
    __slots__ = ()
    __wprops__ = {}
    __size__ = 1

    def __init__(self, control, **kwargs):
        super().__init__([control], **kwargs)

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        (control,) = self._controls()
        return control.render(window, width, height)
