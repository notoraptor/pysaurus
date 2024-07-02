from enum import Enum, unique
from typing import List

import pygame
from pygame.event import Event


@unique
class MouseButton(Enum):
    BUTTON_LEFT = pygame.BUTTON_LEFT
    BUTTON_MIDDLE = pygame.BUTTON_MIDDLE
    BUTTON_RIGHT = pygame.BUTTON_RIGHT
    BUTTON_WHEELDOWN = pygame.BUTTON_WHEELDOWN
    BUTTON_WHEELUP = pygame.BUTTON_WHEELUP
    BUTTON_X1 = pygame.BUTTON_X1
    BUTTON_X2 = pygame.BUTTON_X2


class MotionEvent:
    __slots__ = ("_e", "x", "y")

    def __init__(self, event: Event, x=None, y=None):
        self._e = event
        self.x = event.pos[0] if x is None else x
        self.y = event.pos[1] if y is None else y

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
