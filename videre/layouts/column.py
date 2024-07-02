import pygame

from videre.layouts.abstractlayout import AbstractControlsLayout


class Column(AbstractControlsLayout):
    __slots__ = ()

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        total_height = 0
        max_width = 0
        surfaces = []
        for ctrl in self.controls:
            if height is not None and total_height >= height:
                break
            surface = ctrl.render(window, width, None)
            local_width = ctrl.right + 1
            local_height = ctrl.bottom + 1
            surfaces.append((surface, ctrl.x, total_height + ctrl.y))
            total_height += local_height
            max_width = max(max_width, local_width)
        if width is None:
            width = max_width
        else:
            width = min(width, max_width)
        if height is None:
            height = total_height
        else:
            height = min(height, total_height)
        column = self._new_surface(width, height)
        for surface, x, y in surfaces:
            column.blit(surface, (x, y))
        return column
