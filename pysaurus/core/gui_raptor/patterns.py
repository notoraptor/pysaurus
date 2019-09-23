from ctypes import Structure, c_char_p, c_void_p, cast, pointer
from typing import Iterable, List, Optional

from pysaurus.core.gui_raptor import native_imports


class Pattern:
    __slots__ = ['__type', '__native', '__pattern', '__pointer']

    def __init__(self, drawing_type, native_structure):
        # type: (int, Structure) -> None
        self.__type = drawing_type
        self.__native = native_structure
        self.__pattern = native_imports.Pattern(self.__type, cast(pointer(self.__native), c_void_p))
        self.__pointer = pointer(self.__pattern)

    def __update(self):
        for field, _ in self.__native._fields_:
            if hasattr(self, 'get_native_%s' % field):
                value = getattr(self, 'get_native_%s' % field)()
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
    __slots__ = ('x', 'y', 'font', 'content', 'size', 'outline', 'color', 'outlineColor',
                 'bold', 'italic', 'underline', 'strike')

    def __init__(self, x=0, y=0, font="serif", content=None, size=12, outline=0, color="black",
                 outlineColor=None, bold=False, italic=False, underline=False, strike=False):
        super().__init__(native_imports.DRAWING_TYPE_TEXT, native_imports.PatternText())
        self.x = x
        self.y = y
        self.font = font
        self.content = content
        self.size = size
        self.outline = outline
        self.color = color
        self.outlineColor = outlineColor
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.strike = strike


class PatternFrame(Pattern):
    __slots__ = ('x', 'y', 'width', 'height', 'patterns')

    def __init__(self, x=0, y=0, width=0, height=0, patterns=None):
        # type: (float, float, int, int, Optional[Iterable[Pattern]]) -> None
        super().__init__(native_imports.DRAWING_TYPE_SURFACE, native_imports.PatternFrame())
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.patterns = list(patterns) if patterns else []  # type: List[Pattern]

    def get_native_count(self):
        return len(self.patterns)

    def get_native_patterns(self):
        array = [pattern.pointer() for pattern in self.patterns]
        array_type = native_imports.PatternPtr * len(self.patterns)
        return array_type(*array)


class PatternImage(Pattern):
    __slots__ = ('x', 'y', 'width', 'height', 'src')

    def __init__(self, x=0, y=0, width=-1, height=-1, src=None):
        # type: (float, float, float, float, str) -> None
        super().__init__(native_imports.DRAWING_TYPE_IMAGE, native_imports.PatternImage())
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.src = src


class PatternRectangle(Pattern):
    __slots__ = ('x', 'y', 'width', 'height', 'outline', 'color', 'outlineColor')

    def __init__(self, x=0, y=0, width=0, height=0, outline=0, color=None, outlineColor=None):
        # type: (float, float, float, float, float, str, str) -> None
        super().__init__(native_imports.DRAWING_TYPE_RECTANGLE, native_imports.PatternRectangle())
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.outline = outline
        self.color = color
        self.outlineColor = outlineColor
