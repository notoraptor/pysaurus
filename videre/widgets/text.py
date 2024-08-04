import pygame

from videre.core.events import TextAlign, TextWrap
from videre.core.pygame_font_factory import FONT_FACTORY
from videre.widgets.widget import Widget


class Text(Widget):
    __wprops__ = {"text", "size", "wrap", "align"}
    __slots__ = ()

    def __init__(
        self, text="", size=0, wrap=TextWrap.NONE, align=TextAlign.NONE, **kwargs
    ):
        super().__init__(**kwargs)
        self._set_wprops(text=text, size=size, wrap=wrap, align=align)

    @property
    def text(self) -> str:
        return self._get_wprop("text")

    @property
    def size(self) -> int:
        return self._get_wprop("size")

    @property
    def wrap(self) -> TextWrap:
        return self._get_wprop("wrap")

    @wrap.setter
    def wrap(self, wrap: TextWrap):
        self._set_wprop("wrap", wrap)

    @property
    def align(self) -> TextAlign:
        return self._get_wprop("align")

    @align.setter
    def align(self, align: TextAlign):
        self._set_wprop("align", align)

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        wrap = self.wrap
        if wrap == TextWrap.NONE:
            return FONT_FACTORY.render_text(self.text, None, self.size, compact=True)
        elif wrap == TextWrap.CHAR:
            return FONT_FACTORY.render_text(
                self.text, width, self.size, compact=True, align=self.align
            )
        else:
            return FONT_FACTORY.render_text_wrap_words(
                self.text, width, self.size, compact=True, align=self.align
            )
