from pysaurus.core.classes import Context
from pysaurus.other.native.gui_raptor import symbols, rendering


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
