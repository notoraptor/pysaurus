from ctypes import pointer
from typing import List

from pysaurus.core.gui_raptor import native_imports
from pysaurus.core.gui_raptor.rendering import Render
from pysaurus.core.meta.context import Context


def window_draw(window, drawings):
    # type: (native_imports.Window, List[Render]) -> None
    objects = [render.drawing for render in drawings]
    pointers = [pointer(drawing) for drawing in objects]
    count = len(drawings)
    array_type = native_imports.DrawingPtr * count
    array_object = array_type(*pointers)
    return native_imports.WindowDraw(window, array_object, count)


class Event(Context):
    __slots__ = ['event']

    def __init__(self):
        super().__init__()
        self.event = native_imports.EventNew()

    def on_exit(self):
        native_imports.EventDelete(self.event)

    def is_closed(self):
        return native_imports.EventClosed(self.event)


class Window(Context):
    __slots__ = ['window']

    def __init__(self, width, height, title=None):
        super().__init__()
        self.window = native_imports.WindowNew(width, height, title)

    def on_exit(self):
        native_imports.WindowDelete(self.window)

    def is_open(self):
        # type: () -> bool
        return native_imports.WindowIsOpen(self.window)

    def close(self):
        native_imports.WindowClose(self.window)

    def next_event(self, event):
        # type: (Event) -> bool
        return native_imports.WindowNextEvent(self.window, event.event)

    def draw(self, renders):
        # type: (List[Render]) -> None
        return window_draw(self.window, renders)
