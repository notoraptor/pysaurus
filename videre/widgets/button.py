from videre.layouts.div import Div, OnClickType
from videre.widgets.text import Text


class Button(Div):
    __wprops__ = {"text"}
    __slots__ = ("_text",)

    def __init__(self, text: str, on_click: OnClickType = None, square=False, **kwargs):
        self._text = Text(text.strip(), height_delta=0)
        super().__init__(
            self._text,
            style={"default": {"square": square}},
            on_click=on_click,
            **kwargs
        )

    @property
    def text(self) -> str:
        return self._text.text

    @text.setter
    def text(self, text: str):
        self._text.text = text.strip()

    @property
    def on_click(self) -> OnClickType:
        return self._on_click

    @on_click.setter
    def on_click(self, callback: OnClickType):
        if self._on_click is not callback:
            self._on_click = callback
            self.update()
