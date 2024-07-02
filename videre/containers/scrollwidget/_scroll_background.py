import pygame

from videre.widgets.widget import Widget


class _ScrollBackground(Widget):
    __attributes__ = {"thickness", "both", "hover"}
    __slots__ = ("_h",)
    _COLOR_HOVER = pygame.Color(0, 0, 0, 16)
    _COLOR_NORMAL = pygame.Color(0, 0, 0, 0)

    def __init__(self, horizontal=True, **kwargs):
        super().__init__(**kwargs)
        self._h = horizontal

    def configure(self, thickness: int, both: bool, hover: bool):
        self._set_attribute("thickness", thickness)
        self._set_attribute("both", both)
        self._set_attribute("hover", hover)

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        assert width and height

        thickness = self._get_attribute("thickness")
        both = self._get_attribute("both")
        hover = self._get_attribute("hover")

        if self._h:
            b_width = max(0, width - thickness) if both else width
            b_height = thickness
            self.x, self.y = 0, height - thickness
        else:
            b_width = thickness
            b_height = max(0, height - thickness) if both else height
            self.x, self.y = width - thickness, 0

        surface = pygame.Surface((b_width, b_height), flags=pygame.SRCALPHA)
        surface.fill(self._COLOR_HOVER if hover else self._COLOR_NORMAL)
        return surface
