from typing import Callable, Optional

import pygame
import pygame.gfxdraw

from videre import Colors, Gradient, MotionEvent, MouseButton
from videre.widgets.widget import Widget

_OnClick = Callable[[Widget], None]


class Button(Widget):
    __wprops__ = {"text", "on_click", "color"}
    __slots__ = ("_hover", "_down", "_padx", "_pady")
    _PAD_X = 6
    _PAD_Y = 4
    _COLOR_DEFAULT = Colors.white
    _COLOR_HOVER = Colors.lightgray
    _COLOR_DOWN = Colors.gray

    def __init__(self, text: str, on_click: _OnClick = None, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.on_click = on_click
        self._hover = False
        self._down = False
        self._padx = self._PAD_X
        self._pady = self._PAD_Y
        self._set_color()

    @property
    def text(self) -> str:
        return self._get_wprop("text")

    @text.setter
    def text(self, text: str):
        self._set_wprop("text", text.strip())

    @property
    def on_click(self) -> _OnClick:
        return self._get_wprop("on_click")

    @on_click.setter
    def on_click(self, callback: _OnClick):
        self._set_wprop("on_click", callback)

    @property
    def color(self) -> pygame.Color:
        return self._get_wprop("color")

    def _set_color(self):
        if self._down:
            color = self._COLOR_DOWN
        elif self._hover:
            color = self._COLOR_HOVER
        else:
            color = self._COLOR_DEFAULT
        self._set_wprop("color", color)

    def handle_click(self, button: MouseButton):
        on_click = self.on_click
        if on_click:
            on_click(self)

    def handle_mouse_enter(self, event: MotionEvent):
        self._hover = True
        self._set_color()

    def handle_mouse_exit(self):
        self._hover = False
        self._set_color()

    def handle_mouse_down(self, button: MouseButton, x: int, y: int):
        self._down = True
        self._set_color()

    def handle_mouse_up(self, button: MouseButton, x: int, y: int):
        return self.handle_mouse_down_canceled(button)

    def handle_mouse_down_canceled(self, button: MouseButton):
        self._down = False
        self._set_color()

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        if width is None and height is None:
            text_width = width
            text_surface = self._get_text_surface(window, text_width)
            bg_w = text_surface.get_width() + 2 * (self._padx + 1)
            bg_h = text_surface.get_height() + 2 * (self._pady + 1)
        elif width is None:
            text_width = width
            text_surface = self._get_text_surface(window, text_width)
            bg_w = text_surface.get_width() + 2 * (self._padx + 1)
            bg_h = height
        elif height is None:
            text_width = max(0, width - 2 * (self._padx + 1))
            text_surface = self._get_text_surface(window, text_width)
            bg_w = width
            bg_h = text_surface.get_height() + 2 * (self._pady + 1)
        else:
            text_width = max(0, width - 2 * (self._padx + 1))
            text_surface = self._get_text_surface(window, text_width)
            bg_w = width
            bg_h = height

        text_crop = pygame.Rect(
            0,
            0,
            min(text_surface.get_width(), max(0, bg_w - 2 * (self._padx + 1))),
            min(text_surface.get_height(), max(0, bg_h - 2 * (self._pady + 1))),
        )
        bg = Gradient(self.color).generate(bg_w, bg_h)
        text_x = (bg.get_width() - text_surface.get_width()) // 2
        text_y = (bg.get_height() - text_surface.get_height()) // 2
        bg.blit(text_surface, (text_x, text_y), area=text_crop)
        # Draw borders
        pygame.gfxdraw.rectangle(
            bg, pygame.Rect(0, 0, bg.get_width(), bg.get_height()), Colors.black
        )
        # Done
        return bg

    def _get_text_surface(self, window, width: Optional[int] = None) -> pygame.Surface:
        return window.fonts.render_text(self.text, width, height_delta=0)
