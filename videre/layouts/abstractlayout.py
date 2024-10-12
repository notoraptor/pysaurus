from typing import Callable, List, Optional, Sequence

from videre.core.mouse_ownership import MouseOwnership
from videre.widgets.widget import Widget


class AbstractLayout(Widget):
    __wprops__ = {"_controls"}
    __size__ = None
    __slots__ = ()

    def __init__(self, controls: Sequence[Widget] = (), **kwargs):
        super().__init__(**kwargs)
        self._set_controls(controls)

    def _set_controls(self, controls: Sequence[Widget]):
        if self._get_wprop("_controls") == controls:
            return
        if self.__size__ is not None and len(controls) != self.__size__:
            raise RuntimeError(
                f"[{type(self).__name__}] expects exactly {self.__size__} children"
            )
        for old_control in self._controls() or ():
            old_control.with_parent(None)
        self._set_wprop("_controls", [ctrl.with_parent(self) for ctrl in controls])

    def _controls(self) -> List[Widget]:
        return self._get_wprop("_controls")

    def get_mouse_owner(
        self, x_in_parent: int, y_in_parent: int
    ) -> Optional[MouseOwnership]:
        if super().get_mouse_owner(x_in_parent, y_in_parent):
            local_x, local_y = self.get_local_coordinates(x_in_parent, y_in_parent)
            return get_top_mouse_owner(local_x, local_y, self._controls())
        return None

    def get_mouse_wheel_owner(
        self, x_in_parent: int, y_in_parent: int
    ) -> Optional[MouseOwnership]:
        if self._get_mouse_owner(x_in_parent, y_in_parent):
            local_x, local_y = self.get_local_coordinates(x_in_parent, y_in_parent)
            return get_top_mouse_wheel_owner(local_x, local_y, self._controls())
        return None

    def collect_matchs(self, callback: Callable[[Widget], bool]) -> List[Widget]:
        matchs = super().collect_matchs(callback)
        for control in self._controls():
            matchs.extend(control.collect_matchs(callback))
        return matchs

    def has_changed(self) -> bool:
        return super().has_changed() or any(
            ctrl.has_changed() for ctrl in self._controls()
        )


class AbstractControlsLayout(AbstractLayout):
    __slots__ = ()

    @property
    def controls(self) -> List[Widget]:
        return self._controls()

    @controls.setter
    def controls(self, controls: Sequence[Widget]):
        self._set_controls(controls)


def get_top_mouse_owner(
    x: int, y: int, controls: Sequence[Widget]
) -> Optional[MouseOwnership]:
    for ctrl in reversed(controls):
        owner = ctrl.get_mouse_owner(x, y)
        if owner is not None:
            return owner
    return None


def get_top_mouse_wheel_owner(
    x: int, y: int, controls: Sequence[Widget]
) -> Optional[MouseOwnership]:
    for ctrl in reversed(controls):
        owner = ctrl.get_mouse_wheel_owner(x, y)
        if owner is not None:
            return owner
    return None
