from typing import Callable, Optional

import pygame
import pygame.gfxdraw

from videre import MouseButton
from videre.colors import Colors, Gradient
from videre.utils.pygame_font_factory import FONT_FACTORY
from videre.widgets.widget import Widget

_OnClick = Callable[[Widget], None]


class Button(Widget):
    __wprops__ = {"text", "on_click"}
    __slots__ = ()
    _PADDING_X = 6
    _PADDING_Y = 4

    def __init__(self, text: str, on_click: _OnClick = None, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.on_click = on_click

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

    def handle_click(self, button: MouseButton):
        on_click = self.on_click
        if on_click:
            on_click(self)

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        if width is None and height is None:
            text_surface = self._get_text_surface(width, height)
            bg_width = text_surface.get_width() + 2 * (self._PADDING_X + 1)
            bg_height = text_surface.get_height() + 2 * (self._PADDING_Y + 1)
            bg = Gradient(Colors.white).generate(bg_width, bg_height)
            text_x = (bg.get_width() - text_surface.get_width()) // 2
            text_y = (bg.get_height() - text_surface.get_height()) // 2
            bg.blit(text_surface, (text_x, text_y))
        elif width is None:
            text_surface = self._get_text_surface(width, height)
            bg_width = text_surface.get_width() + 2 * (self._PADDING_X + 1)
            bg_height = min(
                height, text_surface.get_height() + 2 * (self._PADDING_Y + 1)
            )
            bg = Gradient(Colors.white).generate(bg_width, bg_height)
            text_x = (bg.get_width() - text_surface.get_width()) // 2
            text_y = (bg.get_height() - text_surface.get_height()) // 2
            bg.blit(
                text_surface,
                (text_x, text_y),
                area=pygame.Rect(
                    0,
                    0,
                    text_surface.get_width(),
                    min(
                        text_surface.get_height(),
                        max(0, bg_height - 2 * (self._PADDING_Y + 1)),
                    ),
                ),
            )
        elif height is None:
            text_width = max(0, width - 2 * (self._PADDING_X + 1))
            text_surface = self._get_text_surface(text_width, height)
            bg_width = width
            bg_height = text_surface.get_height() + 2 * (self._PADDING_Y + 1)
            bg = Gradient(Colors.white).generate(bg_width, bg_height)
            text_x = (bg.get_width() - text_surface.get_width()) // 2
            text_y = (bg.get_height() - text_surface.get_height()) // 2
            bg.blit(text_surface, (text_x, text_y))
        else:
            text_width = max(0, width - 2 * (self._PADDING_X + 1))
            text_surface = self._get_text_surface(text_width, height)
            bg_width = width
            bg_height = height
            bg = Gradient(Colors.white).generate(bg_width, bg_height)
            text_x = (bg.get_width() - text_surface.get_width()) // 2
            text_y = (bg.get_height() - text_surface.get_height()) // 2
            bg.blit(
                text_surface,
                (text_x, text_y),
                area=pygame.Rect(
                    0,
                    0,
                    min(text_surface.get_width(), bg_width - 2 * (self._PADDING_X + 1)),
                    min(
                        text_surface.get_height(),
                        max(0, bg_height - 2 * (self._PADDING_Y + 1)),
                    ),
                ),
            )

        # Draw borders
        pygame.gfxdraw.rectangle(
            bg, pygame.Rect(0, 0, bg.get_width(), bg.get_height()), Colors.black
        )
        # Done
        return bg

    def _get_text_surface(
        self, width: Optional[int] = None, height: Optional[int] = None
    ) -> pygame.Surface:
        return FONT_FACTORY.render_text(
            self.text, width, size=18, height_delta=0, color=Colors.pink, compact=True
        )
