import logging

import pygame
import pygame.freetype

from pysaurus.core.unicode_utils import Unicode
from resource.fonts import FontProvider


class PygameFontFactory:
    def __init__(self, size=24, origin=True):
        self._prov = FontProvider()
        self.name_to_font = {}
        self.size = size
        self.origin = origin

    def lorem_ipsum(self) -> str:
        return self._prov.lorem_ipsum()

    def get_font(self, c: str) -> pygame.freetype.Font:
        block = Unicode.block(c)
        name, path = self._prov.get_font_info(block)
        if name not in self.name_to_font:
            font = pygame.freetype.Font(path, size=self.size)
            font.origin = self.origin
            self.name_to_font[name] = font
            logging.debug(f"[pygame][font](block={block}) {name}")
        return self.name_to_font[name]

    def _get_tasks_wrap_chars(self, text: str, width: int, size: int = 0):
        first_font = self.get_font(text[0])
        line_spacing = first_font.get_sized_height(size) + 2
        x, y = 0, line_spacing

        height = 0
        tasks = []
        for c in text:
            font = self.get_font(c)
            bounds = font.get_rect(c, size=size)
            ((_, _, _, _, horizontal_advance_x, _),) = font.get_metrics(c, size=size)
            if x + bounds.width + bounds.x >= width:
                x, y = 0, y + line_spacing

            tasks.append((c, font, x, y))
            x += horizontal_advance_x
            height = max(height, y + bounds.height - bounds.y)

        return x, height, tasks

    def render_wrap_chars_0(
        self, text: str, width: int = None, size: int = 0
    ) -> pygame.Surface:
        concrete_width = float("inf") if width is None else width
        new_width, height, tasks = self._get_tasks_wrap_chars(
            text, concrete_width, size
        )
        if width is None:
            width = new_width
        else:
            assert new_width <= width
        color = pygame.Color(255, 255, 0, 128)
        background = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        background.fill(color)
        for c, font, x, y in tasks:
            font.render_to(background, (x, y), c, size=size)
        return background

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


FONT_FACTORY = PygameFontFactory()
