import logging
from abc import ABC, abstractmethod
from typing import Any, Iterable, List, Optional, Tuple

import pygame
import pygame.freetype
import pygame.transform

from videre.colors import Colors
from videre.core.constants import TextAlign
from videre.core.fontfactory.font_factory_utils import (
    CharTask,
    Line,
    WordTask,
    WordsLine,
    align_words,
)
from videre.core.fontfactory.pygame_font_factory import PygameFontFactory


class FontSizes:
    __slots__ = ("height_delta", "line_spacing", "ascender", "descender", "space_width")

    def __init__(self, base_font: pygame.freetype.Font, size: int, height_delta=2):
        self.height_delta = height_delta
        self.line_spacing = base_font.get_sized_height(size) + height_delta
        self.ascender = abs(base_font.get_sized_ascender(size)) + 1
        self.descender = abs(base_font.get_sized_descender(size))
        self.space_width = base_font.get_rect(" ", size=size).width


class RenderedText:
    __slots__ = ("lines", "surface", "font_sizes")

    def __init__(
        self,
        lines: List[Line[WordTask]],
        surface: pygame.Surface,
        font_sizes: FontSizes,
    ):
        self.lines = lines
        self.surface = surface
        self.font_sizes = font_sizes

    def first_x(self) -> int:
        if self.lines:
            line = self.lines[0]
            if line.elements:
                return line.elements[0].x
        return 0


class PygameTextRendering:

    def __init__(
        self,
        fonts: PygameFontFactory,
        size=0,
        strong=False,
        italic=False,
        underline=False,
        height_delta=2,
    ):
        size = size or fonts.size
        height_delta = 2 if height_delta is None else height_delta

        self._fonts = fonts
        self._size = size
        self._strong = bool(strong)
        self._italic = bool(italic)
        self._underline = bool(underline)

        self._height_delta = height_delta
        self._font_sizes = FontSizes(fonts.base_font, size, height_delta)

    def _get_font(self, text: str):
        font = self._fonts.get_font(text)
        try:
            font.strong = self._strong
            font.oblique = self._italic
        except Exception as exc:
            logging.warning(
                f'Unable to set strong or italic for font "{font.name}": '
                f"{type(exc).__name__}: {exc}"
            )
        return font

    def render_char(self, c: str) -> pygame.Surface:
        surface, box = self._get_font(c).render(c, size=self._size)
        return surface

    def render_text(
        self,
        text: str,
        width: int = None,
        *,
        compact=True,
        color: pygame.Color = None,
        align=TextAlign.LEFT,
        wrap_words=False,
    ) -> RenderedText:
        if width is None or not wrap_words:
            new_width, height, char_lines = self._get_char_tasks(text, width, compact)
            lines = WordsLine.from_chars(char_lines, align == TextAlign.NONE)
        else:
            new_width, height, lines = self._get_word_tasks(text, width, compact)
        surface = self._render_word_lines(new_width, height, lines, align, color)
        return RenderedText(lines, surface, self._font_sizes)

    def _render_word_lines(
        self,
        width: int,
        height: int,
        lines: List[Line[WordTask]],
        align: TextAlign,
        color: pygame.Color,
    ) -> pygame.Surface:
        align_words(lines, width, align)
        size = self._size
        out = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        for line in lines:
            self._draw_underline(line, out, color)
            y = line.y
            for word in line.elements:
                x = word.x
                for ch in word.tasks:
                    ch.font.render_to(
                        out, (x + ch.x, y), ch.el, size=size, fgcolor=color
                    )
        return out

    def _draw_underline(self, line: Line[WordTask], out: pygame.Surface, color):
        if self._underline and line:
            c = "_"
            x1 = line.elements[0].x + line.elements[0].tasks[0].bounds.x
            x2 = line.limit()
            font = self._get_font(c)
            font.antialiased = False
            surface, box = font.render(
                c, size=self._size, fgcolor=color or Colors.black
            )
            font.antialiased = True
            us = surface.convert_alpha()
            width = x2 - x1
            height = box.height
            underline = pygame.transform.smoothscale(us, (width, height))
            out.blit(underline, (x1, line.y - box.y))

    def _get_char_tasks(
        self, text: str, width: Optional[int], compact: bool
    ) -> Tuple[int, int, List[Line[CharTask]]]:
        width = float("inf") if width is None else width
        text_factory = Characters(self)
        return self._get_tasks(text_factory, text, width, compact)

    def _get_word_tasks(
        self, text: str, width: int, compact: bool
    ) -> Tuple[int, int, List[Line[WordTask]]]:
        text_factory = Words(self)
        return self._get_tasks(text_factory, text, width, compact)

    def _get_tasks[
        T
    ](self, tel: "TextElements[T]", text: str, width: int, compact: bool) -> Tuple[
        int, int, List[Line[T]]
    ]:
        lines = []
        task_line = tel.newline()
        x = 0
        for el in tel.text_to_elements(text):
            info = tel.parse_element(el)
            if info.is_newline():
                lines.append(task_line)
                task_line = tel.newline(newline=True)
                x = 0
            elif info.is_printable():
                if x and x + info.width > width:
                    lines.append(task_line)
                    task_line = tel.newline()
                    x = 0
                task_line.add(info.at(x))
                x += info.horizontal_shift
        # Add remaining line if necessary
        if task_line:
            lines.append(task_line)
        # Compute width, height and ys
        new_width, height = self._get_text_dimensions(lines, compact)
        return new_width, height, lines

    def _get_text_dimensions(self, lines: List[Line], compact: bool) -> Tuple[int, int]:
        # Compute width, height and ys
        new_width, height = 0, 0
        if lines:
            first_line = lines[0]
            first_line.y = (
                self._font_sizes.ascender + self._height_delta
                if compact and first_line.elements
                else self._font_sizes.line_spacing
            )
            for i in range(1, len(lines)):
                lines[i].y = lines[i - 1].y + self._font_sizes.line_spacing
            height = lines[-1].y + self._font_sizes.descender
            new_width = max(
                (line.limit() for line in lines if line.elements), default=0
            )
        return new_width, height

    def parse_char(self, ic: Tuple[int, str]):
        charpos, c = ic
        font = self._get_font(c)

        bounds = font.get_rect(c, size=self._size)
        width = bounds.x + bounds.width

        (metric,) = font.get_metrics(c, size=self._size)
        horizontal_shift = metric[4] if metric else bounds.width

        return CharTask(c, font, width, horizontal_shift, bounds, charpos)

    def parse_word(self, word: str):
        width, height, lines = self._get_char_tasks(word, None, False)
        if width:
            (line,) = lines
            tasks = line.elements
        else:
            tasks = []
        horizontal_shift = width + self._font_sizes.space_width
        return WordTask(width, 0, tasks, height, horizontal_shift)


class TextElements[T](ABC):
    __slots__ = ("rendering",)

    def __init__(self, rendering: PygameTextRendering):
        self.rendering = rendering

    @abstractmethod
    def text_to_elements(self, text: str) -> Iterable[Any]:
        raise NotImplementedError()

    @abstractmethod
    def parse_element(self, element: str) -> T:
        raise NotImplementedError()

    def newline(self, newline=False) -> Line[T]:
        return Line[T](newline=newline)


class Characters(TextElements[CharTask]):
    __slots__ = ()

    def text_to_elements(self, text: str) -> Iterable[Tuple[int, str]]:
        return enumerate(text)

    def parse_element(self, ic: Tuple[int, str]) -> CharTask:
        return self.rendering.parse_char(ic)


class Words(TextElements[WordTask]):
    __slots__ = ()

    def text_to_elements(self, text: str) -> Iterable[str]:
        first_line, *next_lines = text.split("\n")
        words = [word for word in first_line.split(" ") if word]
        for line in next_lines:
            words.append("\n")
            words.extend(word for word in line.split(" ") if word)
        return words

    def parse_element(self, word: str) -> WordTask:
        return self.rendering.parse_word(word)
