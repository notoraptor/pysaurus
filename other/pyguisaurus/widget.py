from abc import abstractmethod
from typing import Any, Optional

import pygame
from other.pyguisaurus.enumerations import MouseButton


class Widget:
    __attributes__ = {"top", "left"}

    __slots__ = (
        "_key",
        "_old",
        "_new",
        "_surface",
        "_old_update",
        "_transient_state",
        "_rc",
    )

    def __init__(self, key=None):
        self._key = key or id(self)
        self._old = {}
        self._new = {}
        self._old_update = ()
        self._transient_state = {}
        self._surface: Optional[pygame.Surface] = None
        self._set_attribute("top", 0)
        self._set_attribute("left", 0)
        self._rc = 0

    def _assert_rendered(self):
        if not self._surface:
            raise RuntimeError("Widget not yet drawn")

    @property
    def top(self) -> int:
        return self._get_attribute("top")

    @property
    def left(self) -> int:
        return self._get_attribute("left")

    @property
    def bottom(self) -> int:
        self._assert_rendered()
        return self.top + self._surface.get_height() - 1

    @property
    def right(self) -> int:
        self._assert_rendered()
        return self.left + self._surface.get_width() - 1

    @property
    def x(self) -> int:
        return self._get_attribute("left")

    @property
    def y(self) -> int:
        return self._get_attribute("top")

    @property
    def rendered_width(self) -> int:
        self._assert_rendered()
        return self._surface.get_width()

    @property
    def rendered_height(self) -> int:
        self._assert_rendered()
        return self._surface.get_height()

    def get_mouse_owner(self, x: int, y: int):
        if (
            self._surface
            and self.left <= x <= self.right
            and self.top <= y <= self.bottom
        ):
            return self
        return None

    def get_mouse_wheel_owner(self, x: int, y: int):
        return self.get_mouse_owner(x, y)

    def __repr__(self):
        return f"[{type(self).__name__}][{self._key}]"

    def _debug(self, *args, **kwargs):
        print(self, *args, **kwargs)

    @classmethod
    def _has_attribute(cls, name: str) -> bool:
        for typ in cls.__mro__:
            attrs = getattr(typ, "__attributes__", ())
            if name in attrs:
                return True
        return False

    @classmethod
    def _assert_attribute(cls, name):
        assert cls._has_attribute(
            name
        ), f"{cls.__name__}: unknown widget attribute: {name}"

    def _set_attribute(self, name: str, value: Any):
        self._assert_attribute(name)
        self._new[name] = value

    def _get_attribute(self, name: str) -> Any:
        self._assert_attribute(name)
        return self._new.get(name)

    def has_changed(self) -> bool:
        return self._old != self._new or self._transient_state

    def render(self, window, width: int = None, height: int = None) -> pygame.Surface:
        new_update = (window, width, height)
        if (
            self._surface is None
            or self._old_update != new_update
            or self.has_changed()
        ):
            self._rc += 1
            self._debug("render", self._rc)
            self._surface = self.draw(*new_update)
        self._old = self._new.copy()
        self._old_update = new_update
        self._transient_state.clear()
        return self._surface

    @abstractmethod
    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        raise NotImplementedError()

    def handle_mouse_wheel(self, x: int, y: int, shift: bool):
        pass

    def handle_click(self, button: MouseButton):
        pass
