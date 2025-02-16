from typing import Optional

import pygame

from videre.colors import ColorDef, parse_color
from videre.core.constants import TextAlign, TextWrap
from videre.core.fontfactory.pygame_text_rendering import RenderedText
from videre.widgets.widget import Widget


class Text(Widget):
    __wprops__ = {
        "text",
        "size",
        "height_delta",
        "wrap",
        "align",
        "color",
        "strong",
        "italic",
        "underline",
    }
    __slots__ = ("_rendered",)

    def __init__(
        self,
        text="",
        size=0,
        height_delta=2,
        wrap=TextWrap.NONE,
        align=TextAlign.NONE,
        color: ColorDef = None,
        strong: bool = False,
        italic: bool = False,
        underline: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._rendered: Optional[RenderedText] = None
        self._set_wprops(size=size, height_delta=height_delta)
        self.text = text
        self.wrap = wrap
        self.align = align
        self.color = color
        self.strong = strong
        self.italic = italic
        self.underline = underline

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
    def height_delta(self) -> int:
        return self._get_wprop("height_delta")

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

    @property
    def strong(self) -> bool:
        return self._get_wprop("strong")

    @strong.setter
    def strong(self, strong: bool):
        self._set_wprop("strong", bool(strong))

    @property
    def italic(self) -> bool:
        return self._get_wprop("italic")

    @italic.setter
    def italic(self, italic: bool):
        self._set_wprop("italic", bool(italic))

    @property
    def underline(self) -> bool:
        return self._get_wprop("underline")

    @underline.setter
    def underline(self, underline: bool):
        self._set_wprop("underline", bool(underline))

    def _text_rendering(self, window):
        from videre.core.fontfactory.pygame_text_rendering import PygameTextRendering

        rendering: PygameTextRendering = window.text_rendering(
            size=self.size,
            strong=self.strong,
            italic=self.italic,
            underline=self.underline,
            height_delta=self.height_delta,
        )
        return rendering

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        wrap = self.wrap
        render_args = dict(text=self.text, color=self.color)
        if wrap == TextWrap.NONE:
            render_args["width"] = None
            render_args["align"] = TextAlign.NONE
        elif wrap == TextWrap.CHAR:
            render_args["width"] = width
            render_args["align"] = self.align
        else:
            render_args["width"] = width
            render_args["align"] = self.align
            render_args["wrap_words"] = True
        self._rendered = self._text_rendering(window).render_text(**render_args)
        return self._rendered.surface
