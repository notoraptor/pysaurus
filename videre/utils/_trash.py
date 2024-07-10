import logging
from collections import namedtuple
from typing import Iterable, List, Optional, Tuple

import pygame
import pygame.freetype
from pygame.freetype import Font as PFFont

from pysaurus.core.unicode_utils import Unicode
from videre import TextAlign
from videre.utils.pygame_font_factory import PygameFontFactory


class CharInfo:
    __slots__ = ("_c", "_font", "_bounds", "x", "y")

    def __init__(self, c: str, font: PFFont, bounds: pygame.Rect, x: int, y: int):
        self._c, self._font, self._bounds, self.x, self.y = c, font, bounds, x, y

    @property
    def c(self) -> str:
        return self._c

    @property
    def font(self) -> PFFont:
        return self._font

    @property
    def width(self) -> int:
        return self._bounds.width

    @property
    def height(self) -> int:
        return self._bounds.height


class CharTask(namedtuple("CharTask", ("c", "font", "x", "bounds"))):
    __slots__ = ()
    c: str
    font: PFFont
    x: int
    bounds: pygame.Rect

    @property
    def limit(self):
        return self.x + self.bounds.x + self.bounds.width

    @property
    def dy(self):
        return self.bounds.height - self.bounds.y


class WordTask0(namedtuple("WordTask", ("w", "h", "tasks"))):
    __slots__ = ()
    w: int
    h: int
    tasks: List[Tuple[str, pygame.freetype.Font, int, int]]


class TaskLines:
    __slots__ = ("_lines",)

    def __init__(self):
        self._lines: List[List[WordTask0]] = [[]]

    def new_line(self):
        self._lines.append([])

    def append(self, w, h, tasks):
        self._lines[-1].append(WordTask0(w, h, tasks))

    def get_line(self, index=0) -> Iterable[WordTask0]:
        return iter(self._lines[index])

    def count_line(self, index=0) -> int:
        return len(self._lines[index])

    def __iter__(self):
        return (task for line in self._lines for word in line for task in word.tasks)

    def align_center(self, width: int):
        for line in self._lines:
            if line:
                assert line[0].tasks[0][-2] == 0
                wt_n = line[-1]
                size = wt_n.tasks[0][-2] + wt_n.w
                remaining = width - size
                if remaining:
                    remaining /= 2
                    for wt in line:
                        for task in wt.tasks:
                            task[-2] += remaining

    def align_right(self, width: int):
        for line in self._lines:
            if line:
                assert line[0].tasks[0][-2] == 0
                wt_n = line[-1]
                size = wt_n.tasks[0][-2] + wt_n.w
                remaining = width - size
                if remaining:
                    for wt in line:
                        for task in wt.tasks:
                            task[-2] += remaining

    def justify(self, width: int):
        paragraphs = []
        p = []
        for line in self._lines:
            if line:
                p.append(line)
            elif p:
                paragraphs.append(p)
                p = []
        if p:
            paragraphs.append(p)

        for paragraph in paragraphs:
            for i in range(len(paragraph) - 1):
                line = paragraph[i]
                if len(line) > 1:
                    assert line[0].tasks[0][-2] == 0
                    remaining = width - sum(wt.w for wt in line)
                    if remaining:
                        interval = remaining / (len(line) - 1)
                        x = line[0].w + interval
                        for j in range(1, len(line)):
                            wt = line[j]
                            x0 = wt.tasks[0][-2]
                            for task in wt.tasks:
                                task[-2] = task[-2] - x0 + x
                            x += wt.w + interval


class _PygameFontFactoryTrash(PygameFontFactory):
    def _render_wrap_chars(self, text: str, width: int, height: int) -> pygame.Surface:
        color = pygame.Color(255, 255, 0, 128)

        background = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        background.fill(color)

        first_font = self.get_font(text[0])
        line_spacing = first_font.get_sized_height() + 2
        x, y = 0, line_spacing
        for c in text:
            font = self.get_font(c)
            bounds = font.get_rect(c)
            ((_, _, _, _, horizontal_advance_x, _),) = font.get_metrics(c)
            if x + bounds.width + bounds.x >= width:
                x, y = 0, y + line_spacing

            # to check that x (as origin) is out of box
            # x + bounds.width + bounds.x >= width
            # to check that y (as origin) is out of box
            # y + bounds.height - bounds.y >= height

            top_left_y = y - bounds.y
            if top_left_y > height:
                print("out-of-box")
                break

            font.render_to(background, (x, y), None)
            x += horizontal_advance_x

        return background

    def render_text_wrap_words_1(
        self,
        text: str,
        width: int = None,
        size: int = 0,
        height_delta=2,
        compact=False,
        color: pygame.Color = None,
        align=TextAlign.LEFT,
    ) -> pygame.Surface:
        if width is None:
            return self.render_text_1(
                text,
                width,
                size,
                height_delta=height_delta,
                compact=compact,
                color=color,
            )

        words = []
        for i, line in enumerate(text.split("\n")):
            if i > 0:
                words.append("\n")
            words.extend(word for word in line.split(" ") if word)

        size = size or self.size
        first_font = self.get_font(text[0] if text else " ")
        space_bounds = first_font.get_rect(" ", size=size)
        line_spacing = first_font.get_sized_height(size) + height_delta
        x = 0
        new_width = 0

        tl = TaskLines()
        max_y_first_line = 0
        max_dy_first_line = 0

        nb_pieces = len(words)
        cursor = 0
        # Get tasks for first line
        while cursor < nb_pieces:
            word = words[cursor]
            word_w, word_h, word_tasks = self._get_render_tasks_1(
                word, None, size, height_delta, compact
            )
            if word_h and not word_w:
                # \n, new line
                break
            if not word_w:
                # empty word
                cursor += 1
                continue
            if x + word_w > width and (word_w <= width or x > 0):
                break
            else:
                for task in word_tasks:
                    task[-2] += x
                tl.append(word_w, word_h, word_tasks)
                new_width = x + word_w
                x += word_w + space_bounds.width
                word_y = word_tasks[0][-1] if word_tasks else word_h
                max_y_first_line = max(max_y_first_line, word_y)
                max_dy_first_line = max(max_dy_first_line, word_h - word_y)
                cursor += 1

        # Get first line height
        if compact and max_y_first_line:
            max_y_first_line += height_delta
        else:
            max_y_first_line = line_spacing
        for word_task in tl.get_line():
            for task in word_task.tasks:
                task[-1] = max_y_first_line
        y = max_y_first_line if tl.count_line() else 0
        height = y + max_dy_first_line

        while cursor < nb_pieces:
            word = words[cursor]
            cursor += 1
            word_w, word_h, word_tasks = self._get_render_tasks_1(
                word, None, size, height_delta
            )
            if word_h and not word_w:
                # \n
                x, y = 0, y + line_spacing
                height = max(height, y)
                tl.new_line()
                continue
            if not word_w:
                # empty word
                continue
            word_y = word_tasks[0][-1] if word_tasks else word_h
            if x + word_w > width and (word_w <= width or x > 0):
                x, y = 0, y + line_spacing
                tl.new_line()
            for task in word_tasks:
                task[-2] += x
                task[-1] = y
            tl.append(word_w, word_h, word_tasks)
            new_width = max(new_width, x + word_w)
            x += word_w + space_bounds.width
            height = max(height, y + word_h - word_y)

        background = pygame.Surface((new_width, height), flags=pygame.SRCALPHA)
        if color is not None:
            background.fill(color)

        if align != TextAlign.LEFT:
            if align == TextAlign.CENTER:
                tl.align_center(new_width)
            elif align == TextAlign.RIGHT:
                tl.align_right(new_width)
            elif align == TextAlign.JUSTIFY:
                tl.justify(new_width)

        for c, font, cx, cy in tl:
            font.render_to(background, (cx, cy), c, size=size)
        return background

    def render_text_1(
        self,
        text: str,
        width: int = None,
        size: int = 0,
        *,
        height_delta=2,
        compact=False,
        color: pygame.Color = None,
    ) -> pygame.Surface:
        size = size or self.size
        new_width, height, tasks = self._get_render_tasks_1(
            text, width, size, height_delta=height_delta, compact=compact
        )
        background = pygame.Surface((new_width, height), flags=pygame.SRCALPHA)
        if color is not None:
            background.fill(color)
        for c, font, x, y in tasks:
            font.render_to(background, (x, y), c, size=size)
        return background

    def _get_render_tasks_1(
        self,
        text: str,
        width: Optional[int],
        size: int = 0,
        height_delta=2,
        compact=False,
    ):
        width = float("inf") if width is None else width
        line_spacing = (
            self.get_font(text[0] if text else " ").get_sized_height(size)
            + height_delta
        )
        x, new_width = 0, 0

        tasks = []
        max_y_first_line, max_dy_first_line = 0, 0

        # Get tasks for first line
        nb_pieces = len(text)
        cursor = 0
        while cursor < nb_pieces:
            c = text[cursor]
            if c == "\n":
                # First line ends
                break
            if not Unicode.printable(c):
                # Skip
                cursor += 1
                continue

            font = self.get_font(c)
            bounds = font.get_rect(c, size=size)
            if x + bounds.width + bounds.x > width and (
                bounds.x + bounds.width <= width or x > 0
            ):
                # First line ends
                break
            else:
                # Still in first line
                tasks.append([c, font, x, 0])
                new_width = x + bounds.width + bounds.x
                # ((_, _, _, _, h_advance_x, _),) = font.get_metrics(c, size=size)
                (metric,) = font.get_metrics(c, size=size)
                x += metric[4] if metric else bounds.width
                max_y_first_line = max(max_y_first_line, bounds.y)
                max_dy_first_line = max(max_dy_first_line, bounds.height - bounds.y)
                cursor += 1

        # Set first line height
        if compact and max_y_first_line:
            max_y_first_line += height_delta
        else:
            max_y_first_line = line_spacing
        # Set y for first line characters
        for task in tasks:
            task[-1] = max_y_first_line
        # Set y for next characters
        y = max_y_first_line if tasks else 0
        # Initialize render height
        height = y + max_dy_first_line
        logging.debug(
            f"first line height, default {line_spacing} vs {max_y_first_line} "
            f"for {text[: len(tasks)]}"
        )

        # Get tasks for next characters
        for i in range(cursor, nb_pieces):
            c = text[i]
            if c == "\n":
                # Line ends
                x, y = 0, y + line_spacing
                height = max(height, y)
                continue
            if not Unicode.printable(c):
                # Skip
                continue

            font = self.get_font(c)
            bounds = font.get_rect(c, size=size)
            if x + bounds.width + bounds.x > width and (
                bounds.x + bounds.width <= width or x > 0
            ):
                x, y = 0, y + line_spacing

            tasks.append([c, font, x, y])
            new_width = max(new_width, x + bounds.width + bounds.x)
            # ((_, _, _, _, h_advance_x, _),) = font.get_metrics(c, size=size)
            (metric,) = font.get_metrics(c, size=size)
            x += metric[4] if metric else bounds.width
            height = max(height, y + bounds.height - bounds.y)

        return new_width, height, tasks
