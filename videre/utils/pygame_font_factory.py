import logging
from typing import Callable, Union

import pygame
import pygame.freetype

from pysaurus.core.unicode_utils import Unicode
from resource.fonts import FONT_NOTO_REGULAR, FontProvider


class PygameFontFactory:
    def __init__(self, size=14, origin=True, *, overrides=(), use_default_font=False):
        self._prov = FontProvider(overrides=overrides)
        self.name_to_font = {}
        self.size = size
        self.origin = origin

        self.get_font: Callable[[str], pygame.freetype.Font] = None
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
        block = Unicode.block(c)
        name, path = self._prov.get_font_info(block)
        if name not in self.name_to_font:
            font = pygame.freetype.Font(path, size=self.size)
            font.origin = self.origin
            self.name_to_font[name] = font
            logging.debug(f"[pygame][font](block={block}) {name}")
        return self.name_to_font[name]

    def _get_render_tasks(
        self, text: str, width: int, size: int = 0, height_delta=2, compact=False
    ):
        width = float("inf") if width is None else width
        line_spacing = self.get_font(text[0]).get_sized_height(size) + height_delta
        x = 0

        tasks = []
        max_y_first_line = 0
        max_dy_first_line = 0

        # Get tasks for first line
        nb_chars = len(text)
        cursor = 0
        while cursor < nb_chars:
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
            if x + bounds.width + bounds.x >= width:
                # First line ends
                break
            else:
                # Still in first line
                tasks.append([c, font, x, 0])
                # ((_, _, _, _, h_advance_x, _),) = font.get_metrics(c, size=size)
                (metric,) = font.get_metrics(c, size=size)
                h_advance_x = metric[4] if metric else bounds.width
                x += h_advance_x
                max_y_first_line = max(max_y_first_line, bounds.y)
                max_dy_first_line = max(max_dy_first_line, bounds.height - bounds.y)
                cursor += 1

        # Set first line height
        if not compact:
            max_y_first_line = line_spacing
        # Set y for first line characters
        for task in tasks:
            task[-1] = max_y_first_line
        # Set y for next characters
        y = max_y_first_line
        # Initialize render height
        height = y + max_dy_first_line
        logging.debug(
            f"first line height, default {line_spacing} vs {max_y_first_line} "
            f"for {text[: len(tasks)]}"
        )

        # Get tasks for next characters
        while cursor < nb_chars:
            c = text[cursor]
            cursor += 1
            if c == "\n":
                # Line ends
                x, y = 0, y + line_spacing
                continue
            if not Unicode.printable(c):
                # Skip
                continue

            font = self.get_font(c)
            bounds = font.get_rect(c, size=size)
            if x + bounds.width + bounds.x >= width:
                x, y = 0, y + line_spacing

            tasks.append([c, font, x, y])
            # ((_, _, _, _, h_advance_x, _),) = font.get_metrics(c, size=size)
            (metric,) = font.get_metrics(c, size=size)
            h_advance_x = metric[4] if metric else bounds.width
            x += h_advance_x
            height = max(height, y + bounds.height - bounds.y)

        return x, height, tasks

    def render_text(
        self,
        text: str,
        width: int = None,
        size: int = 0,
        height_delta=2,
        compact=False,
        color: pygame.Color = None,
    ) -> pygame.Surface:
        size = size or self.size
        new_width, height, tasks = self._get_render_tasks(
            text, width, size, height_delta=height_delta, compact=compact
        )
        if width is None:
            width = new_width
        else:
            assert new_width <= width
        background = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        if color is not None:
            background.fill(color)
        for c, font, x, y in tasks:
            font.render_to(background, (x, y), c, size=size)
        return background


FONT_FACTORY = PygameFontFactory(overrides=[FONT_NOTO_REGULAR.path])
