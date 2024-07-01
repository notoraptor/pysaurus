from typing import Optional, Sequence, Tuple

from other.pyguisaurus.utils.mouse_ownership import MouseOwnership
from other.pyguisaurus.utils.utils import get_top_mouse_owner, get_top_mouse_wheel_owner
from other.pyguisaurus.widgets.widget import Widget


class Container(Widget):
    __attributes__ = {"_controls"}
    __size__ = None
    __slots__ = ()

    def __init__(self, controls: Sequence[Widget] = (), **kwargs):
        super().__init__(**kwargs)
        self._set_controls(controls)

    def _set_controls(self, controls: Sequence[Widget]):
        if self.__size__ is not None and len(controls) != self.__size__:
            raise RuntimeError(
                f"[{type(self).__name__}] expects exactly {self.__size__} children"
            )
        self._set_attribute(
            "_controls", tuple(ctrl.with_parent(self) for ctrl in controls)
        )

    def _controls(self) -> Tuple[Widget, ...]:
        return self._get_attribute("_controls")

    def get_mouse_owner(self, x: int, y: int) -> Optional[MouseOwnership]:
        if super().get_mouse_owner(x, y):
            local_x, local_y = self.get_local_coordinates(x, y)
            return get_top_mouse_owner(local_x, local_y, self._controls())
        return None

    def get_mouse_wheel_owner(self, x: int, y: int) -> Optional[MouseOwnership]:
        if super().get_mouse_wheel_owner(x, y):
            local_x, local_y = self.get_local_coordinates(x, y)
            return get_top_mouse_wheel_owner(local_x, local_y, self._controls())
        return None

    def has_changed(self) -> bool:
        return super().has_changed() or any(
            ctrl.has_changed() for ctrl in self._controls()
        )
