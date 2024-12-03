import logging
from typing import List, Optional, Tuple

import pygame
import pygame.freetype

from pysaurus.core.unicode_utils import Unicode
from resource.fonts import FontProvider
from videre import TextAlign
from videre.core.fontfactory.font_factory_utils import (
    CharTaskType,
    CharsLine,
    WordTaskType,
    WordsLine,
    align_words,
)
from videre.core.pygame_utils import PygameUtils


class PygameFontFactory(PygameUtils):
    __slots__ = ("_prov", "_name_to_font", "_size", "_origin")

    def __init__(self, size=14, origin=True):
        super().__init__()
        self._prov = FontProvider()
        self._name_to_font = {}
        self._size = size
        self._origin = origin

    @property
    def size(self) -> int:
        return self._size

    @property
    def font_height(self) -> int:
        return self.get_font(" ").get_sized_height(self._size)

    @property
    def symbol_size(self):
        return self._size * 1.625

    def get_font(self, c: str) -> pygame.freetype.Font:
        name, path = self._prov.get_font_info(c)
        font = self._name_to_font.get(name)
        if not font:
            font = pygame.freetype.Font(path, size=self._size)
            font.origin = self._origin
            self._name_to_font[name] = font
            logging.debug(
                f"[pygame][font](block={Unicode.block(c)}, c={c}) {name}, "
                f"height {font.get_sized_height(self._size)}, "
                f"glyph height {font.get_sized_glyph_height(self._size)}, "
                f"ascender {font.get_sized_ascender(self._size)}, "
                f"descender {font.get_sized_descender(self._size)}"
            )
        return font

    def _get_render_tasks(
        self,
        text: str,
        width: Optional[int],
        size: int = 0,
        height_delta=2,
        compact=False,
        line_spacing=0,
    ) -> Tuple[int, int, List[CharsLine]]:
        width = float("inf") if width is None else width

        first_font = self.get_font(" ")
        line_spacing = line_spacing or (
            first_font.get_sized_height(size) + height_delta
        )

        lines: List[CharsLine] = []
        task_line = CharsLine()
        x = 0
        for c in text:
            info = CharTaskType(c, size, self)
            if info.is_newline():
                lines.append(task_line)
                task_line = CharsLine(newline=True)
                x = 0
            elif info.is_printable():
                if x and x + info.width > width:
                    lines.append(task_line)
                    task_line = CharsLine()
                    x = 0
                task_line.tasks.append(info.at(x))
                x += info.horizontal_shift

        if task_line:
            lines.append(task_line)

        # Compute width, height and ys
        new_width, height = 0, 0
        if lines:
            ascender = abs(first_font.get_sized_ascender(size)) + 1
            descender = abs(first_font.get_sized_descender(size))
            first_line = lines[0]
            first_line.y = (
                ascender + height_delta
                if compact and first_line.tasks
                else line_spacing
            )
            for i in range(1, len(lines)):
                lines[i].y = lines[i - 1].y + line_spacing
            height = lines[-1].y + descender
            new_width = max((line.limit() for line in lines if line.tasks), default=0)
        return new_width, height, lines

    def render_char(self, c: str, size: int = 0) -> pygame.Surface:
        font = self.get_font(c)
        surface, box = font.render(c, size=size or self._size)
        return surface

    def _render_text_wrap_chars(
        self,
        text: str,
        width: int = None,
        size: int = 0,
        height_delta=2,
        compact=False,
        color: pygame.Color = None,
        align=TextAlign.LEFT,
    ) -> pygame.Surface:
        size = size or self._size
        new_width, height, lines = self._get_render_tasks(
            text, width, size, height_delta=height_delta, compact=compact
        )
        background = pygame.Surface((new_width, height), flags=pygame.SRCALPHA)

        if align == TextAlign.NONE:
            for line in lines:
                y = line.y
                for ch in line.tasks:
                    ch.font.render_to(
                        background, (ch.x, y), ch.c, size=size, fgcolor=color
                    )
        else:
            word_lines = [WordsLine.from_chars_line(line) for line in lines]
            _render_word_lines(background, word_lines, new_width, size, align, color)
        return background

    def render_text(
        self,
        text: str,
        width: int = None,
        size: int = 0,
        *,
        height_delta=2,
        compact=True,
        color: pygame.Color = None,
        align=TextAlign.LEFT,
        wrap_words=False,
    ) -> pygame.Surface:
        if width is None or not wrap_words:
            return self._render_text_wrap_chars(
                text,
                width,
                size,
                height_delta=height_delta,
                compact=compact,
                color=color,
                align=align,
            )

        first_line, *next_lines = text.split("\n")
        words = [word for word in first_line.split(" ") if word]
        for line in next_lines:
            words.append("\n")
            words.extend(word for word in line.split(" ") if word)

        size = size or self._size
        # Use font for space character to get default spacings
        first_font = self.get_font(" ")
        line_spacing = first_font.get_sized_height(size) + height_delta
        space_w = first_font.get_rect(" ", size=size).width

        lines: List[WordsLine] = []
        task_line = WordsLine()
        x = 0
        for word in words:
            wt = WordTaskType(word, size, height_delta, line_spacing, space_w, self)
            if wt.is_newline():
                # new line
                lines.append(task_line)
                task_line = WordsLine(newline=True)
                x = 0
            elif wt.is_printable():
                if x and x + wt.width > width:
                    lines.append(task_line)
                    task_line = WordsLine()
                    x = 0
                task_line.words.append(wt.at(x))
                x += wt.horizontal_shift

        if task_line:
            lines.append(task_line)

        # Compute width, height and ys
        new_width, height = 0, 0
        if lines:
            ascender = abs(first_font.get_sized_ascender(size)) + 1
            descender = abs(first_font.get_sized_descender(size))
            first_line = lines[0]
            first_line.y = (
                ascender + height_delta
                if compact and first_line.words
                else line_spacing
            )
            for i in range(1, len(lines)):
                lines[i].y = lines[i - 1].y + line_spacing
            height = lines[-1].y + descender
            new_width = max((line.limit() for line in lines if line.words), default=0)

        background = pygame.Surface((new_width, height), flags=pygame.SRCALPHA)
        _render_word_lines(background, lines, new_width, size, align, color)
        return background


def _render_word_lines(
    out: pygame.Surface,
    lines: List[WordsLine],
    width: int,
    size: int,
    align: TextAlign,
    color: pygame.Color,
):
    align_words(lines, width, align)
    for line in lines:
        y = line.y
        for word in line.words:
            x = word.x
            for ch in word.tasks:
                ch.font.render_to(out, (x + ch.x, y), ch.c, size=size, fgcolor=color)
