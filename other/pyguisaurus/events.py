from pygame.event import Event


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
