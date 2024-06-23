from typing import List

from pygame.event import Event

from other.pyguisaurus.enumerations import MouseButton


class MotionEvent:
    __slots__ = ("_e",)

    def __init__(self, event: Event):
        self._e = event

    @property
    def x(self) -> int:
        return self._e.pos[0]

    @property
    def y(self) -> int:
        return self._e.pos[1]

    @property
    def dx(self) -> int:
        return self._e.rel[0]

    @property
    def dy(self) -> int:
        return self._e.rel[1]

    @property
    def button_left(self) -> int:
        return self._e.buttons[0]

    @property
    def button_middle(self) -> int:
        return self._e.buttons[1]

    @property
    def button_right(self) -> int:
        return self._e.buttons[2]

    @property
    def buttons(self) -> List[MouseButton]:
        buttons = []
        if self.button_left:
            buttons.append(MouseButton.BUTTON_LEFT)
        if self.button_right:
            buttons.append(MouseButton.BUTTON_RIGHT)
        if self.button_middle:
            buttons.append(MouseButton.BUTTON_MIDDLE)
        return buttons
