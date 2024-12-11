from typing import List

import pygame
from pygame.event import Event

from videre import MouseButton


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


class KeyboardEntry:
    __slots__ = ("_mod", "_key", "unicode")

    def __init__(self, event: pygame.event.Event):
        self._mod = event.mod
        self._key = event.key
        self.unicode = event.unicode

    lshift = property(lambda self: self._mod & pygame.KMOD_LSHIFT)
    rshift = property(lambda self: self._mod & pygame.KMOD_RSHIFT)
    lctrl = property(lambda self: self._mod & pygame.KMOD_LCTRL)
    rctrl = property(lambda self: self._mod & pygame.KMOD_RCTRL)
    ralt = property(lambda self: self._mod & pygame.KMOD_RALT)
    lalt = property(lambda self: self._mod & pygame.KMOD_LALT)

    backspace = property(lambda self: self._key == pygame.K_BACKSPACE)
    tab = property(lambda self: self._key == pygame.K_TAB)
    enter = property(lambda self: self._key == pygame.K_RETURN)
    escape = property(lambda self: self._key == pygame.K_ESCAPE)
    delete = property(lambda self: self._key == pygame.K_DELETE)
    up = property(lambda self: self._key == pygame.K_UP)
    down = property(lambda self: self._key == pygame.K_DOWN)
    left = property(lambda self: self._key == pygame.K_LEFT)
    right = property(lambda self: self._key == pygame.K_RIGHT)
    home = property(lambda self: self._key == pygame.K_HOME)
    end = property(lambda self: self._key == pygame.K_END)
    pageup = property(lambda self: self._key == pygame.K_PAGEUP)
    pagedown = property(lambda self: self._key == pygame.K_PAGEDOWN)
    printscreen = property(lambda self: self._key == pygame.K_PRINTSCREEN)

    @property
    def caps(self) -> int:
        return self._mod & pygame.KMOD_CAPS

    @property
    def ctrl(self) -> int:
        return self._mod & pygame.KMOD_CTRL

    @property
    def alt(self) -> int:
        return self._mod & pygame.KMOD_ALT

    @property
    def shift(self) -> int:
        return self._mod & pygame.KMOD_SHIFT

    def __repr__(self):
        return " + ".join(
            key for key in ("caps", "ctrl", "alt", "shift") if getattr(self, key)
        )
