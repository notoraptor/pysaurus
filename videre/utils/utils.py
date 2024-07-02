from typing import Optional, Sequence

from videre.utils.mouse_ownership import MouseOwnership
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
