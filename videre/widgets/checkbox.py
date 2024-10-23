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

from videre import MouseButton
from videre.widgets.abstract_check_button import AbstractCheckButton


class Checkbox(AbstractCheckButton):
    __wprops__ = {"on_change"}
    __slots__ = ()

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
        return self._get_checked()

    @checked.setter
    def checked(self, value: bool):
        self._set_checked(value)

    @property
    def on_change(self) -> Optional[Callable[["Checkbox"], None]]:
        return self._get_wprop("on_change")

    @on_change.setter
    def on_change(self, callback: Optional[Callable[["Checkbox"], None]]):
        self._set_wprop("on_change", callback)

    def handle_click(self, button: MouseButton):
        super().handle_click(button)
        on_change = self.on_change
        if on_change:
            on_change(self)
