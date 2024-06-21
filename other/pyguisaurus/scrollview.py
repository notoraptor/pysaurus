from typing import Tuple

import pygame

from other.pyguisaurus.container import Container
from other.pyguisaurus.enumerations import MouseButton
from other.pyguisaurus.widget import Widget

_DEFAULT_SCROLL_STEP = 120
_DEFAULT_SCROLL_COLOR = pygame.Color(216, 216, 216)


class ScrollView(Container):
    __attributes__ = {
        "scroll_thickness",
        "horizontal_scroll",
        "vertical_scroll",
        "expand_children_horizontal",
        "expand_children_vertical",
    }
    __size__ = 3
    __slots__ = ("_ctrl", "_hscrollbar", "_vscrollbar")
    _SCROLL_COLOR = _DEFAULT_SCROLL_COLOR
    _SCROLL_STEP = _DEFAULT_SCROLL_STEP

    def __init__(
        self,
        control: Widget,
        scroll_thickness=18,
        horizontal_scroll=True,
        vertical_scroll=True,
        expand_children_horizontal=False,
        expand_children_vertical=False,
        **kwargs,
    ):
        self._ctrl = control
        self._hscrollbar = _HScrollBar(
            thickness=scroll_thickness, on_jump=self.on_jump_x
        )
        self._vscrollbar = _VScrollBar(
            thickness=scroll_thickness, on_jump=self.on_jump_y
        )
        super().__init__([control, self._hscrollbar, self._vscrollbar], **kwargs)
        self._set_attribute("scroll_thickness", scroll_thickness)
        self._set_attribute("horizontal_scroll", horizontal_scroll)
        self._set_attribute("vertical_scroll", vertical_scroll)
        self._set_attribute("expand_children_horizontal", expand_children_horizontal)
        self._set_attribute("expand_children_vertical", expand_children_vertical)

    def on_jump_x(self, content_x: int):
        self._content_x = -content_x
        self._transient_state["redraw"] = True

    def on_jump_y(self, content_y: int):
        self._content_y = -content_y
        self._transient_state["redraw"] = True

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

        self._content_x, has_h_scroll = self._update_content_pos(
            width,
            content_w,
            self._content_x,
            self._transient_state.get("h"),
            scroll_allowed=self.horizontal_scroll,
        )

        self._content_y, has_v_scroll = self._update_content_pos(
            height,
            content_h,
            self._content_y,
            self._transient_state.get("v"),
            scroll_allowed=self.vertical_scroll,
        )

        view = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        view.blit(content, (self._content_x, self._content_y))

        both = has_h_scroll and has_v_scroll
        if has_h_scroll:
            self._hscrollbar.configure(content_w, self._content_x, both)
            h_scroll = self._hscrollbar.render(window, width, height)
            view.blit(h_scroll, (self._hscrollbar.x, self._hscrollbar.y))
        if has_v_scroll:
            self._vscrollbar.configure(content_h, self._content_y, both)
            v_scroll = self._vscrollbar.render(window, width, height)
            view.blit(v_scroll, (self._vscrollbar.x, self._vscrollbar.y))

        print(
            (width, height), (self._content_x, self._content_y), (content_w, content_h)
        )
        return view

    @classmethod
    def _update_content_pos(
        cls,
        view_length,
        content_length,
        content_pos,
        step_count=None,
        *,
        scroll_allowed=True,
        step_size=_DEFAULT_SCROLL_STEP,
    ) -> Tuple[int, bool]:

        if content_length <= view_length:
            content_pos = 0
        elif content_pos > 0:
            content_pos = 0
        elif content_pos + content_length - 1 < view_length - 1:
            content_pos = view_length - content_length

        if step_count is not None:
            step = step_size * step_count
            if step > 0:
                # scroll left
                content_pos = min(content_pos + step, 0)
            else:
                # scroll right
                content_pos = max(content_pos + step, view_length - content_length)

        scrollbar_is_visible = content_length > view_length and scroll_allowed
        return content_pos, scrollbar_is_visible


class _HScrollBar(Widget):
    __attributes__ = {"content_length", "content_pos", "thickness", "both"}
    __slots__ = ("on_jump",)

    def __init__(self, thickness=18, on_jump=None, **kwargs):
        super().__init__(**kwargs)
        self._set_attribute("thickness", thickness)
        self.on_jump = on_jump

    def configure(self, content_length: int, content_pos: int, both: bool):
        self._set_attribute("content_length", content_length)
        self._set_attribute("content_pos", content_pos)
        self._set_attribute("both", both)

    @property
    def content_length(self) -> int:
        return self._get_attribute("content_length")

    @property
    def content_pos(self) -> int:
        return self._get_attribute("content_pos")

    @property
    def thickness(self) -> int:
        return self._get_attribute("thickness")

    @property
    def both(self) -> bool:
        return self._get_attribute("both")

    def _bar_length(self) -> int:
        w = self._prev_scope_width()
        if self.both:
            w = max(0, w - self.thickness)
        return w

    def get_mouse_owner(self, x: int, y: int):
        if (
            self._surface
            and 0 <= x < self._bar_length()
            and self.y <= y < self.y + self.thickness
        ):
            return self
        return None

    def handle_mouse_down(self, button: MouseButton, x: int, y: int):
        if self.on_jump and button == MouseButton.BUTTON_LEFT:
            grip_length = self._surface.get_width()
            w = self._bar_length()
            if x < self.x or x >= self.x + grip_length:
                x = min(x, w - grip_length)
                content_pos = (x * self.content_length) // w
                self.on_jump(content_pos)

    def _compute(
        self, view_width: int, view_height: int
    ) -> Tuple[pygame.Surface, Tuple[int, int]]:
        thickness = self.thickness
        h_scroll_x, h_scroll_width = self._compute_scroll_metrics(
            view_width,
            self.content_length,
            self.content_pos,
            scrollbar_length=(max(0, view_width - thickness) if self.both else None),
        )
        h_scroll = pygame.Surface((h_scroll_width, thickness))
        h_scroll.fill(_DEFAULT_SCROLL_COLOR)
        pos = (h_scroll_x, view_height - thickness)
        return h_scroll, pos

    @classmethod
    def _compute_scroll_metrics(
        cls, view_length, content_length, content_pos, *, scrollbar_length=None
    ) -> Tuple[int, int]:
        if scrollbar_length is None:
            scrollbar_length = view_length
        scroll_pos = (scrollbar_length * abs(content_pos)) // content_length
        scroll_length = (scrollbar_length * view_length) // content_length
        return scroll_pos, scroll_length

    def draw(
        self, window, view_width: int = None, view_height: int = None
    ) -> pygame.Surface:
        assert view_width and view_height
        h_scroll, (self.x, self.y) = self._compute(view_width, view_height)
        return h_scroll


class _VScrollBar(_HScrollBar):
    __slots__ = ()

    def _bar_length(self) -> int:
        h = self._prev_scope_height()
        if self.both:
            h = max(0, h - self.thickness)
        return h

    def get_mouse_owner(self, x: int, y: int):
        if (
            self._surface
            and self.x <= x < self.x + self.thickness
            and 0 <= y < self._bar_length()
        ):
            return self
        return None

    def handle_mouse_down(self, button: MouseButton, x: int, y: int):
        if self.on_jump and button == MouseButton.BUTTON_LEFT:
            grip_length = self._surface.get_height()
            h = self._bar_length()
            if y < self.y or y >= self.y + grip_length:
                y = min(y, h - grip_length)
                content_pos = (y * self.content_length) // h
                self.on_jump(content_pos)

    def _compute(self, view_width: int, view_height: int):
        thickness = self.thickness
        v_scroll_y, v_scroll_height = self._compute_scroll_metrics(
            view_height,
            self.content_length,
            self.content_pos,
            scrollbar_length=(max(0, view_height - thickness) if self.both else None),
        )
        v_scroll = pygame.Surface((thickness, v_scroll_height))
        v_scroll.fill(_DEFAULT_SCROLL_COLOR)
        pos = (view_width - thickness, v_scroll_y)
        return v_scroll, pos
