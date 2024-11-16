from typing import Optional

import pygame

from videre.colors import ColorDef, parse_color
from videre.core.constants import TextAlign, TextWrap
from videre.widgets.widget import Widget


class Text(Widget):
    __wprops__ = {"text", "size", "wrap", "align", "color"}
    __slots__ = ()

    def __init__(
        self,
        text="",
        size=0,
        wrap=TextWrap.NONE,
        align=TextAlign.NONE,
        color: ColorDef = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._set_wprops(size=size)
        self.text = text
        self.wrap = wrap
        self.align = align
        self.color = color

    @property
    def text(self) -> str:
        return self._get_wprop("text")

    @text.setter
    def text(self, text: str):
        self._set_wprop("text", text)

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

    @property
    def color(self) -> Optional[pygame.Color]:
        return self._get_wprop("color")

    @color.setter
    def color(self, color: ColorDef):
        self._set_wprop("color", None if color is None else parse_color(color))

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        wrap = self.wrap
        render_args = dict(text=self.text, size=self.size, color=self.color)
        if wrap == TextWrap.NONE:
            render_args["width"] = None
        elif wrap == TextWrap.CHAR:
            render_args["width"] = width
            render_args["align"] = self.align
        else:
            render_args["width"] = width
            render_args["align"] = self.align
            render_args["wrap_words"] = True
        return window.fonts.render_text(**render_args)
