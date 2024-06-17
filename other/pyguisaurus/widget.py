from abc import abstractmethod
from typing import Any, Optional

import pygame


class Widget:
    __attributes__ = ()

    __slots__ = ("_key", "_old", "_new", "_surface", "_old_update")

    def __init__(self, key=None):
        self._key = key or id(self)
        self._old = {}
        self._new = {}
        self._old_update = ()
        self._surface: Optional[pygame.Surface] = None

    def _debug(self, *args, **kwargs):
        print(f"[{type(self).__name__}][{self._key}]", *args, **kwargs)

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

    def render(self, window, width: int = None, height: int = None) -> pygame.Surface:
        new_update = (window, width, height)
        if (
            self._surface is None
            or self._old != self._new
            or self._old_update != new_update
        ):
            self._debug("render")
            self._surface = self.draw(*new_update)
        self._old = self._new.copy()
        self._old_update = new_update
        return self._surface

    @abstractmethod
    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        raise NotImplementedError()
