from ctypes import Structure, c_char_p, c_void_p, cast, pointer
from typing import Iterable, List, Optional

from pysaurus.native.gui_raptor import symbols, scheme


def get_ctypes(cls):
    return {name: c_type for name, c_type in cls._fields_}


class Pattern:
    __slots__ = ["__type", "__native", "__pattern", "__pointer"]
    __scheme__ = scheme.Scheme
    __pattern__ = symbols.NoPattern
    __ctypes__ = get_ctypes(symbols.NoPattern)

    def __init__(self, drawing_type):
        # type: (int) -> None
        self.__type = drawing_type
        self.__native = self.__pattern__()
        self.__pattern = symbols.Pattern(
            self.__type, cast(pointer(self.__native), c_void_p)
        )
        self.__pointer = pointer(self.__pattern)

    def __update(self):
        for field, _ in self.__native._fields_:
            if hasattr(self, "get_native_%s" % field):
                value = getattr(self, f"get_native_{field}")()
            else:
                value = getattr(self, field)
                if isinstance(value, str):
                    value = c_char_p(value.encode())
            setattr(self.__native, field, value)

    def pointer(self):
        self.__update()
        return self.__pointer

    def native_pointer(self):
        self.__update()
        return pointer(self.__native)


class PatternText(Pattern):
    __slots__ = (
        "x",
        "y",
        "font",
        "content",
        "size",
        "outline",
        "color",
        "outline_color",
        "bold",
        "italic",
        "underline",
        "strike",
    )
    __scheme__ = scheme.Text
    __pattern__ = symbols.PatternText

    def __init__(
        self,
        x=0,
        y=0,
        font="serif",
        content=None,
        size=12,
        outline=0,
        color="black",
        outline_color=None,
        bold=False,
        italic=False,
        underline=False,
        strike=False,
    ):
        super().__init__(symbols.DRAWING_TYPE_TEXT)
        self.x = x
        self.y = y
        self.font = font
        self.content = content
        self.size = size
        self.outline = outline
        self.color = color
        self.outline_color = outline_color
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.strike = strike

    def get_native_outlineColor(self):
        return self.outline_color


class PatternFrame(Pattern):
    __slots__ = ("x", "y", "width", "height", "patterns")
    __scheme__ = scheme.Frame
    __pattern__ = symbols.PatternFrame

    def __init__(self, x=0, y=0, width=0, height=0, patterns=None):
        # type: (float, float, int, int, Optional[Iterable[Pattern]]) -> None
        super().__init__(symbols.DRAWING_TYPE_SURFACE)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.patterns = list(patterns) if patterns else []  # type: List[Pattern]

    def get_native_count(self):
        return len(self.patterns)

    def get_native_patterns(self):
        array = [pattern.pointer() for pattern in self.patterns]
        array_type = symbols.PatternPtr * len(self.patterns)
        return array_type(*array)


class PatternImage(Pattern):
    __slots__ = ("x", "y", "width", "height", "src")
    __scheme__ = scheme.Image
    __pattern__ = symbols.PatternImage

    def __init__(self, x=0, y=0, width=-1, height=-1, src=None):
        # type: (float, float, float, float, str) -> None
        super().__init__(symbols.DRAWING_TYPE_IMAGE)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.src = src


class PatternRectangle(Pattern):
    __slots__ = ("x", "y", "width", "height", "outline", "color", "outline_color")
    __scheme__ = scheme.Rectangle
    __pattern__ = symbols.PatternRectangle

    def __init__(
        self, x=0, y=0, width=0, height=0, outline=0, color=None, outline_color=None
    ):
        # type: (float, float, float, float, float, str, str) -> None
        super().__init__(symbols.DRAWING_TYPE_RECTANGLE)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.outline = outline
        self.color = color
        self.outline_color = outline_color

    def get_native_outlineColor(self):
        return self.outline_color
