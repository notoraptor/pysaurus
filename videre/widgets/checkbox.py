from typing import Optional

import pygame

from videre import MouseButton
from videre.widgets.abstract_button import AbstractButton


class Checkbox(AbstractButton):
    __wprops__ = {"checked"}
    __slots__ = ()
    _TEXT_0 = "☐"
    _TEXT_1 = "☑"
    _PAD_X = 0
    _PAD_Y = 0
    _BORDER_SIZE = 0

    def __init__(self, checked=False, **kwargs):
        super().__init__("", **kwargs)
        self.checked = checked

    @property
    def checked(self) -> bool:
        return self._get_wprop("checked")

    @checked.setter
    def checked(self, checked: bool):
        self._set_wprop("checked", bool(checked))

    def _compute_checked_text(self) -> str:
        return self._TEXT_1 if self.checked else self._TEXT_0

    def handle_click(self, button: MouseButton):
        self.checked = not self.checked

    def _get_text_surface(self, window, width: Optional[int] = None) -> pygame.Surface:
        return window.fonts.render_char(
            self._compute_checked_text(), size=window.fonts.size * 2
        )
