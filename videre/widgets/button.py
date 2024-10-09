from typing import Callable

from videre import MouseButton
from videre.widgets.abstract_button import AbstractButton
from videre.widgets.widget import Widget

_OnClick = Callable[[Widget], None]


class Button(AbstractButton):
    __wprops__ = {"on_click"}
    __slots__ = ()

    def __init__(self, text: str, on_click: _OnClick = None, **kwargs):
        super().__init__(text, **kwargs)
        self.on_click = on_click

    @property
    def text(self) -> str:
        return self._get_text()

    @text.setter
    def text(self, text: str):
        self._set_text(text)

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
