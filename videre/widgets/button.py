from typing import Callable, Optional

import pygame

from videre import MouseButton
from videre.widgets.abstract_button import AbstractButton


class Button(AbstractButton):
    __wprops__ = {"text", "on_click"}
    __slots__ = ("_text_size",)

    def __init__(
        self,
        text: str,
        on_click: Optional[Callable[["Button"], None]] = None,
        square=False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._text_size = 0
        self.text = text
        self.on_click = on_click
        self.square = square

    @property
    def text(self) -> str:
        return self._get_wprop("text")

    @text.setter
    def text(self, text: str):
        self._set_wprop("text", text.strip())

    @property
    def on_click(self) -> Optional[Callable[["Button"], None]]:
        return self._get_wprop("on_click")

    @on_click.setter
    def on_click(self, callback: Optional[Callable[["Button"], None]]):
        self._set_wprop("on_click", callback)

    @property
    def square(self) -> bool:
        return self._get_square()

    @square.setter
    def square(self, square: bool):
        self._set_square(square)

    def handle_click(self, button: MouseButton):
        on_click = self.on_click
        if on_click:
            on_click(self)

    def _get_text_surface(self, window, width: Optional[int] = None) -> pygame.Surface:
        return (
            window.text_rendering(size=self._text_size, height_delta=0)
            .render_text(self.text, width)
            .surface
        )
