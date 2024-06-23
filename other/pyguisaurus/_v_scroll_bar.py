from typing import Tuple

import pygame

from other.pyguisaurus._h_scroll_bar import _HScrollBar
from other.pyguisaurus.enumerations import MouseButton
from other.pyguisaurus.events import MotionEvent


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
                self._jump(y, h, grip_length)
            else:
                self._grabbed = (y - self.y,)

    def handle_mouse_down_move(self, event: MotionEvent):
        if self.on_jump and self._grabbed and event.button_left:
            grab_y = event.y
            y = grab_y - self._grabbed[0]
            h = self._bar_length()
            grip_length = self._surface.get_height()
            y = min(max(y, 0), h - grip_length)
            if y != self.y:
                self._jump(y, h, grip_length)

    def _jump(self, y: int, h: int, grip_length: int):
        if y == h - grip_length:
            self.on_jump(self.content_length)
        else:
            content_pos = (y * self.content_length) / h
            self.on_jump(round(content_pos))

    def _compute(
        self, view_width: int, view_height: int
    ) -> Tuple[pygame.Surface, Tuple[int, int]]:
        thickness = self.thickness
        v_scroll_y, v_scroll_height = self._compute_scroll_metrics(
            view_height,
            self.content_length,
            self.content_pos,
            scrollbar_length=(max(0, view_height - thickness) if self.both else None),
        )
        v_scroll = pygame.Surface((thickness, v_scroll_height))
        v_scroll.fill(self._SCROLL_COLOR)
        pos = (view_width - thickness, v_scroll_y)
        return v_scroll, pos
