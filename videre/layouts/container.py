from typing import Optional

import pygame
import pygame.gfxdraw

from videre.colors import ColorDefinition, parse_color
from videre.core.constants import Alignment
from videre.core.sides.border import Border
from videre.core.sides.padding import Padding
from videre.layouts.abstractlayout import AbstractLayout
from videre.widgets.empty_widget import EmptyWidget
from videre.widgets.widget import Widget


class Container(AbstractLayout):
    __wprops__ = {
        "border",
        "padding",
        "background_color",
        "vertical_alignment",
        "horizontal_alignment",
        "width",
        "height",
    }
    __slots__ = {}
    __size__ = 1

    def __init__(
        self,
        control: Optional[Widget] = None,
        border: Optional[Border] = None,
        padding: Optional[Padding] = None,
        background_color: ColorDefinition = None,
        vertical_alignment: Alignment = Alignment.START,
        horizontal_alignment: Alignment = Alignment.START,
        width: int = None,
        height: int = None,
        **kwargs
    ):
        super().__init__([control or EmptyWidget()], **kwargs)
        self.border = border
        self.padding = padding
        self.background_color = background_color
        self.vertical_alignment = vertical_alignment
        self.horizontal_alignment = horizontal_alignment
        self.width = width
        self.height = height

    @property
    def control(self) -> Widget:
        (control,) = self._controls()
        return control

    @control.setter
    def control(self, control: Optional[Widget]):
        self._set_controls([control or EmptyWidget()])

    @property
    def border(self) -> Border:
        return self._get_wprop("border")

    @border.setter
    def border(self, border: Optional[Border]):
        self._set_wprop("border", border or Border())

    @property
    def padding(self) -> Padding:
        return self._get_wprop("padding")

    @padding.setter
    def padding(self, padding: Optional[Padding]):
        self._set_wprop("padding", padding or Padding())

    @property
    def background_color(self) -> pygame.Color:
        return self._get_wprop("background_color")

    @background_color.setter
    def background_color(self, color: ColorDefinition):
        self._set_wprop("background_color", parse_color(color))

    @property
    def horizontal_alignment(self) -> Alignment:
        return self._get_wprop("horizontal_alignment")

    @horizontal_alignment.setter
    def horizontal_alignment(self, alignment: Alignment):
        self._set_wprop("horizontal_alignment", alignment)

    @property
    def vertical_alignment(self) -> Alignment:
        return self._get_wprop("vertical_alignment")

    @vertical_alignment.setter
    def vertical_alignment(self, alignment: Alignment):
        self._set_wprop("vertical_alignment", alignment)

    @property
    def width(self) -> int | None:
        return self._get_wprop("width")

    @width.setter
    def width(self, width: int | None):
        self._set_wprop("width", width)

    @property
    def height(self) -> int | None:
        return self._get_wprop("height")

    @height.setter
    def height(self, height: int | None):
        self._set_wprop("height", height)

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        width = _resolve_size(self.width, width)
        height = _resolve_size(self.height, height)
        padding = self.padding
        border = self.border
        margin = padding + border.margin()
        print("padding", padding)
        print("border", border)
        print("Margins", margin)
        print("Total margin", margin.total())
        print("background color", self.background_color)

        min_width = border.left.width + border.right.width
        min_height = border.top.width + border.bottom.width

        control = self.control

        if width is None and height is None:
            # no size available
            inner_surface = control.render(window, width, height)
            inner_width = inner_surface.get_width()
            inner_height = inner_surface.get_height()
            outer_width = margin.get_outer_width(inner_width)
            outer_height = margin.get_outer_height(inner_height)
        elif width is None:
            # height available
            outer_height = max(height, min_height)
            inner_height = margin.get_inner_height(height)
            inner_surface = control.render(window, None, inner_height)
            inner_width = inner_surface.get_width()
            outer_width = margin.get_outer_width(inner_width)
        elif height is None:
            # width available
            outer_width = max(width, min_width)
            inner_width = margin.get_inner_width(width)
            inner_surface = control.render(window, inner_width, None)
            inner_height = inner_surface.get_height()
            outer_height = margin.get_outer_height(inner_height)
        else:
            # width and height available
            outer_width = max(width, min_width)
            outer_height = max(height, min_height)
            inner_width = margin.get_inner_width(width)
            inner_height = margin.get_inner_height(height)
            inner_surface = control.render(window, inner_width, inner_height)

        x = self._align_dim(
            inner_width, inner_surface.get_width(), self.horizontal_alignment
        )
        y = self._align_dim(
            inner_height, inner_surface.get_height(), self.vertical_alignment
        )
        inner_box = pygame.Rect(0, 0, inner_width - x, inner_height - y)
        surface = self._new_surface(outer_width, outer_height)
        surface.fill(self.background_color)
        for border_color, border_points in border.describe_borders(
            outer_width, outer_height
        ):
            if border_points:
                pygame.gfxdraw.filled_polygon(surface, border_points, border_color)
        surface.blit(inner_surface, (margin.left + x, margin.top + y), area=inner_box)
        return surface


def _resolve_size(view_size: int | None, parent_size: int | None) -> int | None:
    if view_size is None and parent_size is None:
        return None
    elif view_size is None:
        return parent_size
    elif parent_size is None:
        return view_size
    else:
        return min(view_size, parent_size)
