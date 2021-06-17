from typing import List

from pysaurus.core.classes import Context
from pysaurus.native.gui_raptor import symbols, rendering


class TextInfo(Context):
    __slots__ = ["native"]

    def __init__(self, pattern_text):
        # type: (rendering.PatternText) -> None
        super().__init__()
        self.native = symbols.PatternTextInfoNew(pattern_text.native_pointer())

    def on_exit(self):
        symbols.PatternTextInfoDelete(self.native)

    @property
    def length(self):
        return self.native.contents.length

    @property
    def width(self):
        return self.native.contents.width

    @property
    def height(self):
        return self.native.contents.height

    @property
    def left(self):
        return self.native.contents.left

    @property
    def top(self):
        return self.native.contents.top

    @property
    def coordinates(self):
        return [
            (
                self.native.contents.coordinates[2 * i],
                self.native.contents.coordinates[2 * i + 1],
            )
            for i in range(self.native.contents.length)
        ]


class Event(Context):
    __slots__ = ["event"]

    def __init__(self):
        super().__init__()
        self.event = symbols.EventNew()

    def on_exit(self):
        symbols.EventDelete(self.event)

    def is_closed(self):
        return symbols.EventClosed(self.event)


class Window(Context):
    __slots__ = ["window"]

    def __init__(self, width, height, title=None):
        super().__init__()
        self.window = symbols.WindowNew(width, height, title)

    def on_exit(self):
        symbols.WindowDelete(self.window)

    def is_open(self):
        # type: () -> bool
        return symbols.WindowIsOpen(self.window)

    def close(self):
        symbols.WindowClose(self.window)

    def next_event(self, event):
        # type: (Event) -> bool
        return symbols.WindowNextEvent(self.window, event.event)

    def draw(self, patterns):
        # type: (List[rendering.Pattern]) -> None
        pointers = [pattern.pointer() for pattern in patterns]
        count = len(pointers)
        array_type = symbols.PatternPtr * count
        array_object = array_type(*pointers)
        return symbols.WindowDraw(self.window, array_object, count)
