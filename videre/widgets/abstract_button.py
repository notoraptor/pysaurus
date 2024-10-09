from typing import Optional

import pygame

from videre import Colors, Gradient, MotionEvent, MouseButton
from videre.widgets.widget import Widget


class AbstractButton(Widget):
    __wprops__ = {"_text", "_color"}
    __slots__ = ("_hover", "_down", "_padx", "_pady", "_border_size", "_text_size")
    _PAD_X = 6
    _PAD_Y = 4
    _BORDER_SIZE = 1
    _COLOR_DEFAULT = Colors.white
    _COLOR_HOVER = Colors.lightgray
    _COLOR_DOWN = Colors.gray

    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)
        self._hover = False
        self._down = False
        self._padx = self._PAD_X
        self._pady = self._PAD_Y
        self._border_size = self._BORDER_SIZE
        self._text_size = 0
        self._set_text(text)
        self._set_color()

    def _set_text(self, text: str):
        self._set_wprop("_text", text.strip())

    def _get_text(self) -> str:
        return self._get_wprop("_text")

    @property
    def _color(self) -> pygame.Color:
        return self._get_wprop("_color")

    def _set_color(self):
        if self._down:
            color = self._COLOR_DOWN
        elif self._hover:
            color = self._COLOR_HOVER
        else:
            color = self._COLOR_DEFAULT
        self._set_wprop("_color", color)

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
        _xdec = self._padx + self._border_size
        _ydec = self._pady + self._border_size
        if width is None and height is None:
            text_width = width
            text_surface = self._get_text_surface(window, text_width)
            bg_w = text_surface.get_width() + 2 * _xdec
            bg_h = text_surface.get_height() + 2 * _ydec
        elif width is None:
            text_width = width
            text_surface = self._get_text_surface(window, text_width)
            bg_w = text_surface.get_width() + 2 * _xdec
            bg_h = height
        elif height is None:
            text_width = max(0, width - 2 * _xdec)
            text_surface = self._get_text_surface(window, text_width)
            bg_w = width
            bg_h = text_surface.get_height() + 2 * _ydec
        else:
            text_width = max(0, width - 2 * _xdec)
            text_surface = self._get_text_surface(window, text_width)
            bg_w = width
            bg_h = height

        text_crop = pygame.Rect(
            0,
            0,
            min(text_surface.get_width(), max(0, bg_w - 2 * _xdec)),
            min(text_surface.get_height(), max(0, bg_h - 2 * _ydec)),
        )
        bg = Gradient(self._color).generate(bg_w, bg_h)
        text_x = (bg.get_width() - text_surface.get_width()) // 2
        text_y = (bg.get_height() - text_surface.get_height()) // 2
        bg.blit(text_surface, (text_x, text_y), area=text_crop)
        # Draw borders
        for i in range(self._border_size):
            pygame.gfxdraw.rectangle(
                bg,
                pygame.Rect(i, i, bg.get_width() - 2 * i, bg.get_height() - 2 * i),
                Colors.black,
            )
        # Done
        return bg

    def _get_text_surface(self, window, width: Optional[int] = None) -> pygame.Surface:
        return window.fonts.render_text(
            self._get_text(), width, size=self._text_size, height_delta=0
        )
