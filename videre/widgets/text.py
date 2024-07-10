import pygame

from videre.utils.events import TextAlign, TextWrap
from videre.utils.pygame_font_factory import FONT_FACTORY
from videre.widgets.widget import Widget


class Text(Widget):
    __wprops__ = {"text", "size", "wrap", "align"}
    __slots__ = ()

    def __init__(
        self, text="", size=0, wrap=TextWrap.NONE, align=TextAlign.LEFT, **kwargs
    ):
        super().__init__(**kwargs)
        self._set_wprop("text", text)
        self._set_wprop("size", size)
        self._set_wprop("wrap", wrap)
        self._set_wprop("align", align)

    @property
    def text(self) -> str:
        return self._get_wprop("text")

    @property
    def size(self) -> int:
        return self._get_wprop("size")

    @property
    def wrap(self) -> TextWrap:
        return self._get_wprop("wrap")

    @property
    def align(self) -> TextAlign:
        return self._get_wprop("align")

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        wrap = self.wrap
        if wrap == TextWrap.NONE:
            return FONT_FACTORY.render_text(self.text, None, self.size, compact=True)
        elif wrap == TextWrap.CHAR:
            return FONT_FACTORY.render_text(self.text, width, self.size, compact=True)
        else:
            return FONT_FACTORY.render_text_wrap_words(
                self.text, width, self.size, align=self.align, compact=True
            )
