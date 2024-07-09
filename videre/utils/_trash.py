from collections import namedtuple
from typing import List, Optional, Tuple

import pygame
from pygame.freetype import Font as PFFont

from pysaurus.core.unicode_utils import Unicode
from videre.utils.pygame_font_factory import PygameFontFactory


def _right_limit(c: Tuple[str, PFFont, int, pygame.Rect]) -> int:
    bounds = c[3]
    return c[2] + bounds.x + bounds.width


class TaskLine:
    __slots__ = ("y", "tasks")
    y: int
    tasks: List[Tuple[str, PFFont, int, pygame.Rect]]

    def __init__(self):
        self.y, self.tasks = 0, []


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

    def _get_render_tasks_2(
        self,
        text: str,
        width: Optional[int],
        size: int = 0,
        height_delta=2,
        compact=False,
    ) -> Tuple[int, int, List[TaskLine]]:
        width = float("inf") if width is None else width
        line_spacing = (
            self.get_font(text[0] if text else " ").get_sized_height(size)
            + height_delta
        )

        task_line = TaskLine()
        lines: List[TaskLine] = [task_line]
        x = 0
        for c in text:
            if c == "\n":
                task_line = TaskLine()
                lines.append(task_line)
                x = 0
                continue
            if not Unicode.printable(c):
                continue
            font = self.get_font(c)
            bounds = font.get_rect(c, size=size)
            if x and x + bounds.x + bounds.width > width:
                task_line = TaskLine()
                lines.append(task_line)
                x = 0
            task_line.tasks.append((c, font, x, bounds))
            (metric,) = font.get_metrics(c, size=size)
            x += metric[4] if metric else bounds.width

        new_width, height = 0, 0
        start = 0 if lines[0].tasks else 1
        if len(lines) - start:
            first_line = lines[start]
            first_line.y = (
                max(c[3].y for c in first_line.tasks) + height_delta
                if compact and first_line.tasks
                else line_spacing
            )
            for i in range(start + 1, len(lines)):
                lines[i].y = lines[i - 1].y + line_spacing
            height = lines[-1].y + max(
                (c[3].height - c[3].y for c in lines[-1].tasks), default=0
            )
            new_width = max(
                (
                    _right_limit(lines[i].tasks[-1])
                    for i in range(start, len(lines))
                    if lines[i].tasks
                ),
                default=0,
            )
        return new_width, height, lines

    def render_text_2(
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
        new_width, height, lines = self._get_render_tasks_2(
            text, width, size, height_delta=height_delta, compact=compact
        )
        background = pygame.Surface((new_width, height), flags=pygame.SRCALPHA)
        if color is not None:
            background.fill(color)
        for line in lines:
            y = line.y
            for c, font, x, _ in line.tasks:
                font.render_to(background, (x, y), c, size=size)
        return background


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
