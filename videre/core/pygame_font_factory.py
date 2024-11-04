import logging
from typing import Callable, List, Optional, Tuple, Union

import pygame
import pygame.freetype
from pygame.freetype import Font as PFFont

from pysaurus.core.unicode_utils import Unicode
from resource.fonts import FontProvider
from videre import TextAlign
from videre.core.pygame_utils import PygameUtils

# c, font, x, bounds
CharTaskType = Tuple[str, PFFont, int, pygame.Rect]


class CharsLine:
    __slots__ = ("y", "tasks")
    y: int
    tasks: List[CharTaskType]

    def __init__(self):
        self.y, self.tasks = 0, []

    def limit(self) -> int:
        _, _, x, bounds = self.tasks[-1]
        return x + bounds.x + bounds.width


class WordTask:
    __slots__ = ("w", "x", "tasks")

    def __init__(self, w: int, x: int, tasks: List[CharTaskType]):
        self.w, self.x, self.tasks = w, x, tasks

    def __repr__(self):
        return f"{self.x}:" + repr("".join(t[0] for t in self.tasks))


class WordsLine:
    __slots__ = ("y", "words")
    y: int
    words: List[WordTask]

    def __init__(self, y=0):
        self.y, self.words = y, []

    def __repr__(self):
        return f"({self.y}, {self.words})"

    def limit(self) -> int:
        word = self.words[-1]
        return word.x + word.w

    @classmethod
    def from_chars_line(cls, chars_line: CharsLine):
        words = []
        word = []
        for task in chars_line.tasks:
            if task[0] == " ":
                if word:
                    words.append(word)
                    word = []
            else:
                word.append(task)
        if word:
            words.append(word)
        words_line = cls(chars_line.y)
        if words:
            x0 = words[0][0][-2]
            for word in words:
                w_x = word[0][-2]
                x = w_x - x0
                tasks = [(c, font, cx - w_x, bounds) for c, font, cx, bounds in word]
                _, _, last_x, last_bounds = tasks[-1]
                w = last_x + last_bounds.x + last_bounds.width
                words_line.words.append(WordTask(w, x, tasks))
        return words_line


def align_words(lines: List[WordsLine], width: int, align=TextAlign.LEFT):
    if align == TextAlign.NONE or align == TextAlign.LEFT:
        return
    if align == TextAlign.JUSTIFY:
        return justify_words(lines, width)
    for line in lines:
        if line.words:
            assert line.words[0].x == 0, line
            remaining = width - line.limit()
            if remaining:
                if align == TextAlign.CENTER:
                    remaining /= 2
                for wt in line.words:
                    wt.x += remaining


def justify_words(lines: List[WordsLine], width: int):
    paragraphs = []
    p = []
    for line in lines:
        if line.words:
            p.append(line)
        elif p:
            paragraphs.append(p)
            p = []
    if p:
        paragraphs.append(p)

    for paragraph in paragraphs:
        for i in range(len(paragraph) - 1):
            line = paragraph[i]
            if len(line.words) > 1:
                assert line.words[0].x == 0
                remaining = width - sum(wt.w for wt in line.words)
                if remaining:
                    interval = remaining / (len(line.words) - 1)
                    x = line.words[0].w + interval
                    for j in range(1, len(line.words)):
                        wt = line.words[j]
                        wt.x = x
                        x += wt.w + interval


class PygameFontFactory(PygameUtils):
    def __init__(self, size=14, origin=True, *, use_default_font=False):
        super().__init__()

        self._prov = FontProvider()
        self.name_to_font = {}
        self.size = size
        self.origin = origin

        self.get_font: Callable[[str], pygame.freetype.Font] = self._get_font
        self._default_font = None
        self.set_font_policy(use_default_font=use_default_font)

    @property
    def provider(self) -> FontProvider:
        return self._prov

    def set_font_policy(self, *, use_default_font: Union[None, False, str] = False):
        if use_default_font is not False:
            self._default_font = pygame.freetype.Font(use_default_font, size=self.size)
            self._default_font.origin = self.origin
            self.get_font = self._get_default_font
        else:
            self.get_font = self._get_font

    def _get_default_font(self, c: str) -> pygame.freetype.Font:
        return self._default_font

    def _get_font(self, c: str) -> pygame.freetype.Font:
        name, path = self._prov.get_font_info(c)
        font = self.name_to_font.get(name)
        if not font:
            font = pygame.freetype.Font(path, size=self.size)
            font.origin = self.origin
            self.name_to_font[name] = font
            logging.debug(
                f"[pygame][font](block={Unicode.block(c)}, c={c}) {name}, "
                f"height {font.get_sized_height(self.size)}, "
                f"glyph height {font.get_sized_glyph_height(self.size)}, "
                f"ascender {font.get_sized_ascender(self.size)}, "
                f"descender {font.get_sized_descender(self.size)}"
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
        lines: List[CharsLine] = []

        task_line = CharsLine()
        nb_chars = len(text)
        cursor = 0
        while cursor < nb_chars:
            c = text[cursor]
            if c == "\n" or Unicode.printable(c):
                lines.append(task_line)
                break
            else:
                cursor += 1

        x = 0
        width = float("inf") if width is None else width
        for i in range(cursor, nb_chars):
            c = text[i]
            if c == "\n":
                task_line = CharsLine()
                lines.append(task_line)
                x = 0
                continue
            if not Unicode.printable(c):
                continue
            font = self.get_font(c)
            bounds = font.get_rect(c, size=size)
            if x and x + bounds.x + bounds.width > width:
                task_line = CharsLine()
                lines.append(task_line)
                x = 0
            task_line.tasks.append((c, font, x, bounds))
            (metric,) = font.get_metrics(c, size=size)
            x += metric[4] if metric else bounds.width

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

    def _render_unwrapped_text(
        self,
        text: str,
        width: int = None,
        size: int = 0,
        height_delta=2,
        compact=False,
        color: pygame.Color = None,
        align=TextAlign.LEFT,
    ) -> pygame.Surface:
        size = size or self.size
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
            align_words(word_lines, new_width, align)
            for line in word_lines:
                y = line.y
                for word in line.words:
                    x = word.x
                    for c, font, cx, _ in word.tasks:
                        font.render_to(background, (x + cx, y), c, size=size)
        return background

    def render_char(self, c: str, size: int = 0) -> pygame.Surface:
        font = self.get_font(c)
        surface, box = font.render(c, size=size or self.size)
        return surface

    @property
    def standard_size(self) -> int:
        return self.get_font(" ").get_sized_height(self.size)

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
            return self._render_unwrapped_text(
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

        size = size or self.size
        # Use font for space character to get default spacings
        first_font = self.get_font(" ")
        line_spacing = first_font.get_sized_height(size) + height_delta
        space_w = first_font.get_rect(" ", size=size).width
        ascender = abs(first_font.get_sized_ascender(size)) + 1
        descender = abs(first_font.get_sized_descender(size))

        lines: List[WordsLine] = []
        task_line = WordsLine()

        cursor = 0
        nb_words = len(words)
        while cursor < nb_words:
            word = words[cursor]
            word_w, word_h, _ = self._get_render_tasks(
                word, None, size, height_delta, False, line_spacing
            )
            if word_h or word_w:
                lines.append(task_line)
                break
            else:
                cursor += 1

        x = 0
        for i in range(cursor, nb_words):
            word = words[i]
            word_w, word_h, word_lines = self._get_render_tasks(
                word, None, size, height_delta, False, line_spacing
            )
            if not word_w:
                if word_h:
                    # new line
                    task_line = WordsLine()
                    lines.append(task_line)
                    x = 0
                # new line or empty word, continue anyway
                continue
            if x and x + word_w > width:
                task_line = WordsLine()
                lines.append(task_line)
                x = 0
            (word_line,) = word_lines
            task_line.words.append(WordTask(word_w, x, word_line.tasks))
            x += word_w + space_w

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

        align_words(lines, new_width, align)
        for line in lines:
            y = line.y
            for word in line.words:
                x = word.x
                for c, font, cx, _ in word.tasks:
                    font.render_to(background, (x + cx, y), c, size=size)
        return background
