from typing import Sequence

from other.pyguisaurus.utils import get_top_mouse_owner
from other.pyguisaurus.widget import Widget


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
        self._set_attribute("_controls", controls)

    def _controls(self) -> Sequence[Widget]:
        return self._get_attribute("_controls")

    def get_mouse_owner(self, x: int, y: int):
        if super().get_mouse_owner(x, y):
            return get_top_mouse_owner(x, y, self._controls())
        return None

    def has_changed(self) -> bool:
        return super().has_changed() or any(
            ctrl.has_changed() for ctrl in self._controls()
        )
