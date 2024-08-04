from typing import Optional, Sequence

from videre.core.mouse_ownership import MouseOwnership
from videre.widgets.widget import Widget


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


class Procedure:
    __slots__ = ("proc",)

    def __init__(self, procedure: callable):
        self.proc = procedure

    def __call__(self, widget: Widget):
        return self.proc()


class WidgetSet:
    __slots__ = ("_widget", "_props")

    def __init__(self, widget, **props):
        self._widget = widget
        self._props = props

    def __call__(self, clicked: Widget):
        widget = self._widget
        for name, value in self._props.items():
            setattr(widget, name, value)
