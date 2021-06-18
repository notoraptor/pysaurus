from typing import List

from pysaurus.other.native.gui_raptor import symbols
from pysaurus.other.native.gui_raptor import rendering


class Event:
    @staticmethod
    def new():
        return symbols.EventNew()

    @staticmethod
    def destroy(event):
        symbols.EventDelete(event)

    @staticmethod
    def is_closed(event):
        return symbols.EventClosed(event)


class Window:
    @staticmethod
    def new(width, height, title=None):
        return symbols.WindowNew(width, height, title)

    @staticmethod
    def destroy(window):
        if Window.is_open(window):
            Window.close(window)
        assert not Window.is_open(window)
        symbols.WindowDelete(window)

    @staticmethod
    def is_open(window):
        # type: (object) -> bool
        return symbols.WindowIsOpen(window)

    @staticmethod
    def close(window):
        symbols.WindowClose(window)

    @staticmethod
    def next_event(window, event):
        # type: (object, Event) -> bool
        return symbols.WindowNextEvent(window, event)

    @staticmethod
    def draw(window, patterns):
        # type: (object, List[rendering.Pattern]) -> None
        count = len(patterns)
        array_type = symbols.PatternPtr * count
        return symbols.WindowDraw(
            window, array_type(*[pattern.pointer() for pattern in patterns]), count
        )
