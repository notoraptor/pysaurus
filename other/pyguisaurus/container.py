from typing import Sequence

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
            owners = [ctrl.get_mouse_owner(x, y) for ctrl in self._controls()]
            owners = [ctrl for ctrl in owners if ctrl is not None]
            if owners:
                (owner,) = owners
                return owner
        return None