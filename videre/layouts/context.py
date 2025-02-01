from typing import Self, Union

import pygame

from videre.colors import Colors
from videre.core.sides.border import Border
from videre.layouts.abstractlayout import AbstractLayout
from videre.layouts.container import Container
from videre.widgets.widget import Widget


class Context(AbstractLayout):
    __slots__ = ("_relative",)
    __wprops__ = {}
    __size__ = 1

    def __init__(self, relative: Widget, control: Widget, **kwargs):
        container = Container(
            control, border=Border.all(1), background_color=Colors.white
        )
        self._relative = relative
        super().__init__([container], **kwargs)

    def handle_focus_in(self) -> Union[bool, Self]:
        return self._relative.handle_focus_in()

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        self._relative._assert_rendered()
        (container,) = self._controls()
        x = self._relative.global_x
        y = self._relative.global_y + self._relative.rendered_height

        control_surface = container.render(window, None, None)
        surface = self._new_surface(width, height)
        surface.blit(control_surface, (x, y))
        self._set_child_position(container, x, y)
        return surface
