from typing import Optional

from videre import MouseButton
from videre.widgets.widget import Widget


class EventPropagator:
    @classmethod
    def _handle(
        cls, widget: Widget, handle_function: str, *args, **kwargs
    ) -> Optional[Widget]:
        # print(handle_function, widget)
        if widget:
            if getattr(widget, handle_function)(*args, **kwargs):
                return widget
            else:
                return cls._handle(widget.parent, handle_function, *args, **kwargs)
        else:
            return None

    @classmethod
    def handle_click(cls, widget: Widget, button: MouseButton) -> Optional[Widget]:
        return cls._handle(widget, Widget.handle_click.__name__, button)

    @classmethod
    def handle_focus_in(cls, widget: Widget) -> Optional[Widget]:
        return cls._handle(widget, Widget.handle_focus_in.__name__)

    @classmethod
    def handle_focus_out(cls, widget: Widget) -> Optional[Widget]:
        return cls._handle(widget, Widget.handle_focus_out.__name__)
