import logging
from typing import List, Optional, Tuple

import pygame
import pygame.freetype

from pysaurus.core.unicode_utils import Unicode
from resource.fonts import FontProvider
from videre import TextAlign
from videre.core.fontfactory.font_factory_utils import (
    CharsLine,
    WordTask,
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
        lines: List[CharsLine] = []
        task_line = CharsLine()
        x = 0
        for i, c in enumerate(text):
            if c == "\n":
                lines.append(task_line)
                task_line = CharsLine(newline=True)
                x = 0
            elif Unicode.printable(c):
                font = self.get_font(c)
                bounds = font.get_rect(c, size=size)
                if x and x + bounds.x + bounds.width > width:
                    lines.append(task_line)
                    task_line = CharsLine()
                    x = 0
                task_line.tasks.append((c, font, x, bounds))
                (metric,) = font.get_metrics(c, size=size)
                x += metric[4] if metric else bounds.width

        if task_line:
            lines.append(task_line)

        new_width, height = 0, 0
        if lines:
            # Use font for space character to get default spacings
            first_font = self.get_font(" ")
            ascender = abs(first_font.get_sized_ascender(size)) + 1
            descender = abs(first_font.get_sized_descender(size))
            line_spacing = line_spacing or (
                first_font.get_sized_height(size) + height_delta
            )
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
        if color is not None:
            background.fill(color)

        if align == TextAlign.NONE:
            for line in lines:
                y = line.y
                for c, font, x, _ in line.tasks:
                    font.render_to(background, (x, y), c, size=size)
        else:
            word_lines = [WordsLine.from_chars_line(line) for line in lines]
            _render_word_lines(background, word_lines, new_width, size, align)
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
        ascender = abs(first_font.get_sized_ascender(size)) + 1
        descender = abs(first_font.get_sized_descender(size))

        lines: List[WordsLine] = []
        task_line = WordsLine()
        x = 0
        for i, word in enumerate(words):
            word_w, word_h, word_lines = self._get_render_tasks(
                word, None, size, height_delta, False, line_spacing
            )
            if not word_w:
                if word_h:
                    # new line
                    lines.append(task_line)
                    task_line = WordsLine(newline=True)
                    x = 0
                # new line or empty word, continue anyway
                continue
            if x and x + word_w > width:
                lines.append(task_line)
                task_line = WordsLine()
                x = 0
            (word_line,) = word_lines
            task_line.words.append(WordTask(word_w, x, word_line.tasks))
            x += word_w + space_w

        if task_line:
            lines.append(task_line)

        # Compute width, height and ys
        new_width, height = 0, 0
        if lines:
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
        if color is not None:
            background.fill(color)

        _render_word_lines(background, lines, new_width, size, align)
        return background


def _render_word_lines(
    out: pygame.Surface, lines: List[WordsLine], width: int, size: int, align: TextAlign
):
    align_words(lines, width, align)
    for line in lines:
        y = line.y
        for word in line.words:
            x = word.x
            for c, font, cx, _ in word.tasks:
                font.render_to(out, (x + cx, y), c, size=size)
