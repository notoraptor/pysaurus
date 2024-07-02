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
            print(f"[pygame][font](block={block}) {name}")
        return self.name_to_font[name]

    def _get_tasks_wrap_chars(
        self, text: str, width: int, size: int = 0, height_delta=2, compact=False
    ):
        width = float("inf") if width is None else width

        first_font = self.get_font(text[0])
        line_spacing = first_font.get_sized_height(size) + height_delta
        x = 0

        tasks = []
        max_y_first_line = 0
        max_dy_first_line = 0

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
                ((_, _, _, _, horizontal_advance_x, _),) = font.get_metrics(
                    c, size=size
                )
                x += horizontal_advance_x
                max_y_first_line = max(max_y_first_line, bounds.y)
                max_dy_first_line = max(max_dy_first_line, bounds.height - bounds.y)
                cursor += 1

        if not compact:
            max_y_first_line = line_spacing

        for task in tasks:
            task[-1] = max_y_first_line
        y = max_y_first_line
        height = y + max_dy_first_line
        print(
            "first line height, default",
            line_spacing,
            "vs",
            max_y_first_line,
            "for",
            text[: len(tasks)],
        )

        while cursor < nb_chars:
            c = text[cursor]
            if c == "\n":
                # Line ends
                x, y = 0, y + line_spacing
                cursor += 1
                continue
            if not Unicode.printable(c):
                # Skip
                cursor += 1
                continue

            font = self.get_font(c)
            bounds = font.get_rect(c, size=size)
            if x + bounds.width + bounds.x >= width:
                x, y = 0, y + line_spacing

            tasks.append([c, font, x, y])
            ((_, _, _, _, horizontal_advance_x, _),) = font.get_metrics(c, size=size)
            x += horizontal_advance_x
            height = max(height, y + bounds.height - bounds.y)
            cursor += 1

        return x, height, tasks

    def render_wrap_chars_0(
        self,
        text: str,
        width: int = None,
        size: int = 0,
        height_delta=2,
        compact=False,
        color=None,
    ) -> pygame.Surface:
        size = size or self.size
        new_width, height, tasks = self._get_tasks_wrap_chars(
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
