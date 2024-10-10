"""
https://en.wikipedia.org/wiki/Check_mark
⍻ 	U+237B 	NOT CHECK MARK
☐ 	U+2610 	BALLOT BOX
☑ 	U+2611 	BALLOT BOX WITH CHECK
✅ 	U+2705 	WHITE HEAVY CHECK MARK
✓ 	U+2713 	CHECK MARK
✔ 	U+2714 	HEAVY CHECK MARK
𐄂 	U+10102 	AEGEAN CHECK MARK
𝤿 	U+1D93F 	SIGNWRITING MOVEMENT-WALLPLANE CHECK SMALL
𝥀 	U+1D940 	SIGNWRITING MOVEMENT-WALLPLANE CHECK MEDIUM
𝥁 	U+1D941 	SIGNWRITING MOVEMENT-WALLPLANE CHECK LARGE
🗸 	U+1F5F8 	LIGHT CHECK MARK
🗹 	U+1F5F9 	BALLOT BOX WITH BOLD CHECK
🮱 	U+1FBB1 	INVERSE CHECK MARK
"""
from typing import Callable, Optional

import pygame

from videre import MouseButton
from videre.widgets.abstract_button import AbstractButton


class Checkbox(AbstractButton):
    __wprops__ = {"checked", "on_change"}
    __slots__ = ()
    _PAD_X = 0
    _PAD_Y = 0
    _BORDER_SIZE = 0
    _TEXT_0 = "☐"
    _TEXT_1 = "☑"

    def __init__(
        self,
        checked=False,
        on_change: Optional[Callable[["Checkbox"], None]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.checked = checked
        self.on_change = on_change

    @property
    def checked(self) -> bool:
        return self._get_wprop("checked")

    @checked.setter
    def checked(self, checked: bool):
        self._set_wprop("checked", bool(checked))

    @property
    def on_change(self) -> Optional[Callable[["Checkbox"], None]]:
        return self._get_wprop("on_change")

    @on_change.setter
    def on_change(self, callback: Optional[Callable[["Checkbox"], None]]):
        self._set_wprop("on_change", callback)

    def handle_click(self, button: MouseButton):
        self.checked = not self.checked
        on_change = self.on_change
        if on_change:
            on_change(self)

    def _compute_checked_text(self) -> str:
        return self._TEXT_1 if self.checked else self._TEXT_0

    def _get_text_surface(self, window, width: Optional[int] = None) -> pygame.Surface:
        return window.fonts.render_char(
            self._compute_checked_text(), size=window.fonts.size * 2
        )
