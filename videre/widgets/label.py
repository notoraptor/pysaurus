from typing import Union

from videre import MotionEvent, MouseButton
from videre.widgets.abstract_button import AbstractButton
from videre.widgets.text import Text
from videre.widgets.widget import Widget


class Label(Text):
    __wprops__ = {}
    __slots__ = ["_for_button", "_for_key"]

    def __init__(self, for_button: Union[str, AbstractButton], **kwargs):
        super().__init__(**kwargs)
        if isinstance(for_button, AbstractButton):
            self._for_button = for_button
            self._for_key = for_button.key
        else:
            assert isinstance(for_button, str)
            self._for_button = None
            self._for_key = for_button

    def _get_button(self) -> AbstractButton:
        if self._for_button is None:
            candidates = self.get_root().collect_matchs(
                lambda w: w.key == self._for_key
            )
            if len(candidates) == 1:
                (self._for_button,) = candidates
            else:
                # TODO Warning here ?
                self._for_button = Widget()
        return self._for_button

    def handle_mouse_enter(self, event: MotionEvent):
        button = self._get_button()
        return button.handle_mouse_enter(MotionEvent(event._e, x=button.x, y=button.y))

    def handle_mouse_exit(self):
        return self._get_button().handle_mouse_exit()

    def handle_mouse_down(self, button: MouseButton, x: int, y: int):
        bw = self._get_button()
        return bw.handle_mouse_down(button, bw.x, bw.y)

    def handle_mouse_up(self, button: MouseButton, x: int, y: int):
        bw = self._get_button()
        return bw.handle_mouse_up(button, bw.x, bw.y)

    def handle_mouse_down_canceled(self, button: MouseButton):
        return self._get_button().handle_mouse_down_canceled(button)

    def handle_click(self, button: MouseButton):
        return self._get_button().handle_click(button)
