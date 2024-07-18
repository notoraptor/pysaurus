from collections.abc import Sequence
from typing import List, Optional, Tuple

import pygame

from videre.layouts.abstractlayout import AbstractControlsLayout
from videre.widgets.widget import Widget


class Row(AbstractControlsLayout):
    __wprops__ = {"expand_vertical"}
    __slots__ = ()

    def __init__(self, controls: Sequence[Widget], expand_vertical=True, **kwargs):
        super().__init__(controls, **kwargs)
        self._set_wprop("expand_vertical", expand_vertical)

    @property
    def expand_vertical(self) -> bool:
        return self._get_wprop("expand_vertical")

    @expand_vertical.setter
    def expand_vertical(self, value):
        self._set_wprop("expand_vertical", bool(value))

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        h_hint = height if self.expand_vertical else None
        max_height = 0
        total_width = 0
        controls = self.controls
        rendered: List[Optional[Tuple[Widget, pygame.Surface]]] = [None] * len(controls)

        weights = [ctrl.weight for ctrl in controls]
        total_weight = sum(weights)
        if height is None or total_weight == 0:
            for i, ctrl in enumerate(controls):
                if width is not None and total_width >= width:
                    break
                surface = ctrl.render(window, None, h_hint)
                rendered[i] = (ctrl, surface)
                total_width += surface.get_width()
                max_height = max(max_height, surface.get_height())
        else:
            to_render = []
            for i, ctrl in enumerate(controls):
                if total_width >= width:
                    break
                if weights[i]:
                    to_render.append((i, ctrl))
                else:
                    surface = ctrl.render(window, None, h_hint)
                    rendered[i] = (ctrl, surface)
                    total_width += surface.get_width()
                    max_height = max(max_height, surface.get_height())
            remaining_width = width - total_width
            if remaining_width > 0:
                for i, ctrl in to_render:
                    if total_width >= width:
                        break
                    available_width = remaining_width * weights[i] / total_weight
                    surface = ctrl.render(window, available_width, h_hint)
                    rendered[i] = (ctrl, surface)
                    total_width += surface.get_width()
                    max_height = max(max_height, surface.get_height())

        if width is None:
            width = total_width
        else:
            width = min(width, total_width)
        if height is None:
            height = max_height
        else:
            height = min(height, max_height)
        column = self._new_surface(width, height)
        x = 0
        for render in rendered:
            if render:
                ctrl, surface = render
                column.blit(surface, (x, 0))
                ctrl.x, ctrl.y = x, 0
                x += surface.get_width()
        return column
