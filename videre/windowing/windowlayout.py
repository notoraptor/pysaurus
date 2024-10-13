import pygame

from videre.colors import Colors
from videre.layouts.abstractlayout import AbstractControlsLayout


class WindowLayout(AbstractControlsLayout):
    __slots__ = ()
    _FILL = Colors.white

    def __init__(self, screen: pygame.Surface):
        super().__init__()
        self._surface = screen

    def render(self, window, width: int = None, height: int = None) -> pygame.Surface:
        return super().render(
            window, self._surface.get_width(), self._surface.get_height()
        )

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        screen = self._surface

        screen_width, screen_height = screen.get_width(), screen.get_height()
        screen.fill(self._FILL)
        for control in self.controls:
            surface = control.render(window, screen_width, screen_height)
            screen.blit(surface, (control.x, control.y))

        return screen
