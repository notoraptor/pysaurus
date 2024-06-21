from typing import Tuple

import pygame

from other.pyguisaurus.container import Container
from other.pyguisaurus.widget import Widget

_DEFAULT_SCROLL_STEP = 120


class ScrollView(Container):
    __attributes__ = {
        "scroll_thickness",
        "horizontal_scroll",
        "vertical_scroll",
        "expand_children_horizontal",
        "expand_children_vertical",
    }
    __size__ = 1
    __slots__ = ("_ctrl",)
    _SCROLL_COLOR = pygame.Color(216, 216, 216)
    _SCROLL_STEP = _DEFAULT_SCROLL_STEP

    def __init__(
        self,
        control: Widget,
        scroll_thickness=18,
        horizontal_scroll=True,
        vertical_scroll=True,
        expand_children_horizontal=False,
        expand_children_vertical=False,
        **kwargs
    ):
        super().__init__([control], **kwargs)
        self._set_attribute("scroll_thickness", scroll_thickness)
        self._set_attribute("horizontal_scroll", horizontal_scroll)
        self._set_attribute("vertical_scroll", vertical_scroll)
        self._set_attribute("expand_children_horizontal", expand_children_horizontal)
        self._set_attribute("expand_children_vertical", expand_children_vertical)
        self._ctrl = control

    @property
    def control(self) -> Widget:
        return self._ctrl

    @property
    def _content_x(self) -> int:
        return self._ctrl.x

    @_content_x.setter
    def _content_x(self, x: int):
        self._ctrl.x = x

    @property
    def _content_y(self) -> int:
        return self._ctrl.y

    @_content_y.setter
    def _content_y(self, y: int):
        self._ctrl.y = y

    @property
    def scroll_thickness(self) -> int:
        return self._get_attribute("scroll_thickness")

    @property
    def horizontal_scroll(self) -> bool:
        return self._get_attribute("horizontal_scroll")

    @property
    def vertical_scroll(self) -> bool:
        return self._get_attribute("vertical_scroll")

    @property
    def expand_children_horizontal(self) -> bool:
        return self._get_attribute("expand_children_horizontal")

    @property
    def expand_children_vertical(self) -> bool:
        return self._get_attribute("expand_children_vertical")

    def get_mouse_wheel_owner(self, x: int, y: int):
        if Widget.get_mouse_owner(self, x, y):
            child = self.get_mouse_owner(x, y)
            if isinstance(child, ScrollView):
                return child
            else:
                return self
        return None

    def handle_mouse_wheel(self, x: int, y: int, shift: bool):
        if not x and not y:
            return

        horizontal, vertical = 0, 0
        if x and y:
            horizontal, vertical = x, y
        elif x:
            horizontal = x
        elif shift:
            horizontal = y
        else:
            vertical = y

        if self._can_scroll_horizontal(horizontal):
            self._transient_state["h"] = horizontal
        if self._can_scroll_vertical(vertical):
            self._transient_state["v"] = vertical

    def _can_scroll_horizontal(self, direction) -> bool:
        if not self.horizontal_scroll or not direction:
            return False
        if direction > 0:
            # scroll left
            return self._content_x < 0
        else:
            # scroll right
            return self._content_x > self.rendered_width - self.control.rendered_width

    def _can_scroll_vertical(self, direction) -> bool:
        if not self.vertical_scroll or not direction:
            return False
        if direction > 0:
            # scroll top
            return self._content_y < 0
        else:
            # scroll bottom
            return self._content_y > self.rendered_height - self.control.rendered_height

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        c_w_hint = width if self.expand_children_horizontal else None
        c_h_hint = height if self.expand_children_vertical else None
        content = self.control.render(window, c_w_hint, c_h_hint)
        content_w, content_h = content.get_width(), content.get_height()

        if width is None:
            width = content_w
        if height is None:
            height = content_h

        if (
            width == content_w
            and height == content_h
            and self._content_x == 0
            and self._content_y == 0
        ):
            return content

        if content_w <= width:
            self._content_x = 0
        elif self._content_x > 0:
            self._content_x = 0
        elif self._content_x + content_w - 1 < width - 1:
            self._content_x = width - content_w

        if content_h <= height:
            self._content_y = 0
        elif self._content_y > 0:
            self._content_y = 0
        elif self._content_y + content_h - 1 < height - 1:
            self._content_y = height - content_h

        h_scroll_width = None
        h_scroll_x = None
        v_scroll_height = None
        v_scroll_y = None
        scroll_thickness = self.scroll_thickness

        both = (
            content_w > width
            and self.horizontal_scroll
            and content_h > height
            and self.vertical_scroll
        )

        if content_w > width and self.horizontal_scroll:
            self._content_x, h_scroll_x, h_scroll_width = _compute_scroll_metrics(
                width,
                content_w,
                self._content_x,
                self._transient_state.get("h"),
                scrollbar_length=(max(0, width - scroll_thickness) if both else None),
            )

        if content_h > height and self.vertical_scroll:
            self._content_y, v_scroll_y, v_scroll_height = _compute_scroll_metrics(
                height,
                content_h,
                self._content_y,
                self._transient_state.get("v"),
                scrollbar_length=(max(0, height - scroll_thickness) if both else None),
            )

        view = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        view.blit(content, (self._content_x, self._content_y))
        if h_scroll_width is not None:
            h_scroll = pygame.Surface((h_scroll_width, scroll_thickness))
            h_scroll.fill(self._SCROLL_COLOR)
            view.blit(h_scroll, (h_scroll_x, height - scroll_thickness))
        if v_scroll_height is not None:
            v_scroll = pygame.Surface((scroll_thickness, v_scroll_height))
            v_scroll.fill(self._SCROLL_COLOR)
            view.blit(v_scroll, (width - scroll_thickness, v_scroll_y))

        print(
            (width, height), (self._content_x, self._content_y), (content_w, content_h)
        )
        return view


def _compute_scroll_metrics(
    view_length,
    content_length,
    content_pos,
    step_count=None,
    step_size=_DEFAULT_SCROLL_STEP,
    scrollbar_length=None,
) -> Tuple[int, int, int]:
    if scrollbar_length is None:
        scrollbar_length = view_length
    scroll_length = (scrollbar_length * view_length) // content_length
    if step_count is not None:
        step = step_size * step_count
        if step > 0:
            # scroll left
            content_pos = min(content_pos + step, 0)
        else:
            # scroll right
            content_pos = max(content_pos + step, view_length - content_length)
    scroll_pos = (scrollbar_length * abs(content_pos)) // content_length
    return content_pos, scroll_pos, scroll_length
