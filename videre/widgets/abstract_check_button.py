from typing import Optional

import pygame

from videre.colors import Colors
from videre.core.events import MouseButton
from videre.widgets.abstract_button import AbstractButton


class AbstractCheckButton(AbstractButton):
    __wprops__ = {"_checked", "_strong"}
    __slots__ = ()
    _PAD_X = 0
    _PAD_Y = 0
    _BORDER_SIZE = 0
    _COLOR_HOVER = Colors.transparent
    _COLOR_DOWN = Colors.transparent
    _TEXT_0 = "☐"
    _TEXT_1 = "☑"

    def _get_checked(self) -> bool:
        return self._get_wprop("_checked")

    def _set_checked(self, checked: bool):
        self._set_wprop("_checked", bool(checked))

    def handle_click(self, button: MouseButton):
        self._set_checked(not self._get_checked())

    def _compute_checked_text(self) -> str:
        return self._TEXT_1 if self._get_checked() else self._TEXT_0

    def _get_strong(self):
        return bool(self._get_wprop("_strong"))

    def _set_color(self):
        super()._set_color()
        self._set_wprop("_strong", self._hover)

    def _get_text_surface(self, window, width: Optional[int] = None) -> pygame.Surface:
        return window.text_rendering(
            size=window.fonts.symbol_size, strong=self._get_strong()
        ).render_char(self._compute_checked_text())
