import pygame

from videre.colors import Colors
from videre.layouts.abstract_controls_layout import AbstractControlsLayout


class WindowLayout(AbstractControlsLayout):
    __slots__ = ("_bgc",)
    _FILL = Colors.white

    def __init__(self, screen: pygame.Surface, background: pygame.Color | None = None):
        super().__init__()
        self._surface = screen
        self._bgc = background or self._FILL

    def render(self, window, width: int = None, height: int = None) -> pygame.Surface:
        return super().render(
            window, self._surface.get_width(), self._surface.get_height()
        )

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        screen = self._surface

        screen_width, screen_height = screen.get_width(), screen.get_height()
        screen.fill(self._bgc)
        for control in self.controls:
            surface = control.render(window, screen_width, screen_height)
            screen.blit(surface, (control.x, control.y))

        return screen
