from typing import List

from pysaurus.core.gui_raptor import native_imports, patterns
from pysaurus.core.meta.context import Context


class TextInfo(Context):
    __slots__ = ['native']

    def __init__(self, pattern_text):
        # type: (patterns.PatternText) -> None
        super().__init__()
        self.native = native_imports.PatternTextInfoNew(pattern_text.native_pointer())

    def on_exit(self):
        native_imports.PatternTextInfoDelete(self.native)

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
        return [(self.native.contents.coordinates[2 * i], self.native.contents.coordinates[2 * i + 1])
                for i in range(self.native.contents.length)]


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

    def draw(self, patterns):
        # type: (List[patterns.Pattern]) -> None
        pointers = [pattern.pointer() for pattern in patterns]
        count = len(pointers)
        array_type = native_imports.PatternPtr * count
        array_object = array_type(*pointers)
        return native_imports.WindowDraw(self.window, array_object, count)
