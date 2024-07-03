import pygame

from videre.utils.pygame_font_factory import PygameFontFactory


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
