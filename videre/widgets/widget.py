from abc import abstractmethod
from typing import Any, Optional, Tuple

import pygame

from videre.core.events import MotionEvent, MouseButton
from videre.core.mouse_ownership import MouseOwnership
from videre.core.pygame_utils import PygameUtils


class Widget(PygameUtils):
    __wprops__ = ("weight",)

    __slots__ = (
        "_key",
        "_old",
        "_new",
        "_surface",
        "_old_update",
        "_transient_state",
        "_rc",
        "_parent",
        "x",
        "y",
    )

    def __init__(self, weight=0, parent=None, key=None):
        super().__init__()

        self._key = key or id(self)
        self._old = {}
        self._new = {"weight": weight}
        self._old_update = ()
        self._transient_state = {}
        self._surface: Optional[pygame.Surface] = None
        self._rc = 0
        # Widget coordinates relative to its parent.
        # If parent is None, relative to window.
        self.x = 0
        self.y = 0

        self._parent: Optional[Widget] = None
        if parent:
            self.with_parent(parent)

    def with_parent(self, parent):
        self._parent = parent
        if parent is None:
            self.x = self.y = 0
        return self

    @property
    def weight(self) -> int:
        return self._get_wprop("weight")

    @property
    def parent(self):
        return self._parent

    @property
    def global_x(self) -> int:
        if self._parent:
            return self._parent.global_x + self.x
        return self.x

    @property
    def global_y(self) -> int:
        if self._parent:
            return self._parent.global_y + self.y
        return self.y

    def _assert_rendered(self):
        if not self._surface:
            raise RuntimeError(f"{self} not yet drawn")

    @property
    def top(self) -> int:
        return self.y

    @property
    def left(self) -> int:
        return self.x

    @property
    def pos(self) -> Tuple[int, int]:
        return self.x, self.y

    @property
    def bottom(self) -> int:
        self._assert_rendered()
        return self.top + self._surface.get_height() - 1

    @property
    def right(self) -> int:
        self._assert_rendered()
        return self.left + self._surface.get_width() - 1

    @property
    def rendered_width(self) -> int:
        self._assert_rendered()
        return self._surface.get_width()

    @property
    def rendered_height(self) -> int:
        self._assert_rendered()
        return self._surface.get_height()

    def get_local_coordinates(self, global_x: int, global_y: int) -> Tuple[int, int]:
        return global_x - self.x, global_y - self.y

    def get_mouse_owner(
        self, x_in_parent: int, y_in_parent: int
    ) -> Optional[MouseOwnership]:
        if (
            self._surface
            and self.left <= x_in_parent <= self.right
            and self.top <= y_in_parent <= self.bottom
        ):
            return MouseOwnership(self, x_in_parent, y_in_parent)
        return None

    def get_mouse_wheel_owner(
        self, x_in_parent: int, y_in_parent: int
    ) -> Optional[MouseOwnership]:
        return self.get_mouse_owner(x_in_parent, y_in_parent)

    def __repr__(self):
        return f"[{type(self).__name__}][{self._key}]"

    def _debug(self, *args, **kwargs):
        print(self, *args, **kwargs)

    def _prev_scope_width(self) -> int:
        return self._old_update[1]

    def _prev_scope_height(self) -> int:
        return self._old_update[2]

    @classmethod
    def _has_wprop(cls, name: str) -> bool:
        for typ in cls.__mro__:
            wprops = getattr(typ, "__wprops__", ())
            if name in wprops:
                return True
        return False

    @classmethod
    def _assert_wprop(cls, name):
        assert cls._has_wprop(name), f"{cls.__name__}: unknown widget property: {name}"

    def _set_wprop(self, name: str, value: Any):
        self._assert_wprop(name)
        self._new[name] = value

    def _set_wprops(self, **kwargs):
        for name in kwargs:
            self._assert_wprop(name)
        self._new.update(kwargs)

    def _get_wprop(self, name: str) -> Any:
        self._assert_wprop(name)
        return self._new.get(name)

    def update(self):
        self._transient_state["redraw"] = True

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

    def handle_mouse_enter(self, event: MotionEvent):
        pass

    def handle_mouse_over(self, event: MotionEvent):
        pass

    def handle_mouse_down(self, button: MouseButton, x: int, y: int):
        pass

    def handle_mouse_down_move(self, event: MotionEvent):
        pass

    def handle_mouse_down_canceled(self, button: MouseButton):
        pass

    def handle_mouse_up(self, button: MouseButton, x: int, y: int):
        pass

    def handle_mouse_exit(self):
        pass
