from ctypes import Structure, c_char_p, c_void_p, cast, pointer
from typing import List

from pysaurus.core.gui_raptor import native_imports


class Pattern:
    __slots__ = ['type', 'native', 'pattern', '__pointer']

    def __init__(self, drawing_type, native_structure):
        assert (isinstance(drawing_type, int)
                and 0 <= drawing_type < native_imports.NB_DRAWING_TYPE)
        assert isinstance(native_structure, Structure)
        self.type = drawing_type
        self.native = native_structure
        self.pattern = native_imports.Pattern(
            self.type,
            cast(pointer(self.native), c_void_p)
        )
        self.__pointer = pointer(self.pattern)

    def update(self):
        for field, _ in self.native._fields_:
            if hasattr(self, 'get_native_%s' % field):
                value = getattr(self, 'get_native_%s' % field)()
            else:
                value = getattr(self, field)
                if isinstance(value, str):
                    value = c_char_p(value.encode())
            setattr(self.native, field, value)

    def get_pointer(self):
        self.update()
        return self.__pointer

    def get_native_pointer(self):
        self.update()
        return pointer(self.native)


class PatternText(Pattern):
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
    def __init__(self, x=0, y=0, width=0, height=0, patterns=None):
        super().__init__(native_imports.DRAWING_TYPE_SURFACE, native_imports.PatternFrame())
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.patterns = list(patterns) if patterns else []  # type: List[Pattern]

    def get_native_count(self):
        return len(self.patterns)

    def get_native_patterns(self):
        array = [pattern.get_pointer() for pattern in self.patterns]
        array_type = native_imports.PatternPtr * len(self.patterns)
        return array_type(*array)


class PatternImage(Pattern):
    def __init__(self, *, x=0, y=0, width=-1, height=-1, src=None):
        # type: (None, float, float, int, int, str) -> None
        super().__init__(native_imports.DRAWING_TYPE_IMAGE, native_imports.PatternImage())
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.src = src


class PatternRectangle(Pattern):
    def __init__(self, x=0, y=0, width=0, height=0, outline=0, color=None, outlineColor=None):
        super().__init__(native_imports.DRAWING_TYPE_RECTANGLE, native_imports.PatternRectangle())
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.outline = outline
        self.color = color
        self.outlineColor = outlineColor
