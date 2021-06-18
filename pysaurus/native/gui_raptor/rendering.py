from ctypes import c_char_p, c_void_p, cast, pointer
from typing import Iterable, List, Optional

from pysaurus.native.gui_raptor import symbols


class Pattern:
    __slots__ = ()
    __pattern__ = symbols.NoPattern
    __type__ = None

    def __new_native(self):
        native = self.__pattern__()
        for field, _ in self.__pattern__._fields_:
            if hasattr(self, "get_native_%s" % field):
                value = getattr(self, f"get_native_{field}")()
            else:
                value = getattr(self, field)
                if isinstance(value, str):
                    value = c_char_p(value.encode())
            setattr(native, field, value)
        return native

    def pointer(self):
        return pointer(
            symbols.Pattern(self.__type__, cast(pointer(self.__new_native()), c_void_p))
        )

    def native_pointer(self):
        return pointer(self.__new_native())


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
    __pattern__ = symbols.PatternText
    __type__ = symbols.DRAWING_TYPE_TEXT

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
    __pattern__ = symbols.PatternFrame
    __type__ = symbols.DRAWING_TYPE_SURFACE

    def __init__(self, x=0, y=0, width=0, height=0, patterns=None):
        # type: (float, float, int, int, Optional[Iterable[Pattern]]) -> None
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.patterns = list(patterns) if patterns else []  # type: List[Pattern]

    def get_native_count(self):
        return len(self.patterns)

    def get_native_patterns(self):
        array_type = symbols.PatternPtr * len(self.patterns)
        return array_type(*[pattern.pointer() for pattern in self.patterns])


class PatternImage(Pattern):
    __slots__ = ("x", "y", "width", "height", "src")
    __pattern__ = symbols.PatternImage
    __type__ = symbols.DRAWING_TYPE_IMAGE

    def __init__(self, x=0, y=0, width=-1, height=-1, src=None):
        # type: (float, float, float, float, str) -> None
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.src = src


class PatternRectangle(Pattern):
    __slots__ = ("x", "y", "width", "height", "outline", "color", "outline_color")
    __pattern__ = symbols.PatternRectangle
    __type__ = symbols.DRAWING_TYPE_RECTANGLE

    def __init__(
        self, x=0, y=0, width=0, height=0, outline=0, color=None, outline_color=None
    ):
        # type: (float, float, float, float, float, str, str) -> None
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.outline = outline
        self.color = color
        self.outline_color = outline_color

    def get_native_outlineColor(self):
        return self.outline_color
