from typing import Optional

import pygame

from videre import MouseButton
from videre.widgets.abstract_button import AbstractButton


class AbstractCheckButton(AbstractButton):
    __wprops__ = {"_checked"}
    __slots__ = ()
    _PAD_X = 0
    _PAD_Y = 0
    _BORDER_SIZE = 0
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

    def _get_text_surface(self, window, width: Optional[int] = None) -> pygame.Surface:
        return window.fonts.render_char(
            self._compute_checked_text(), size=window.fonts.size * 2
        )
