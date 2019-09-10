from ctypes import c_char_p, pointer, cast, c_void_p

from pysaurus.core.gui_raptor import native_imports


class Render:
    __slots__ = ['drawing']
    drawing: native_imports.Drawing


class RenderImage(Render):
    __slots__ = ('path', 'x', 'y', 'w', 'h', 'drawing_image')

    def __init__(self, path, x=0, y=0, w=-1, h=-1):
        # type: (str, float, float, int, int) -> None
        self.path = path
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.drawing_image = native_imports.DrawingImage(
            c_char_p(self.path.encode()), self.x, self.y, self.w, self.h)
        self.drawing = native_imports.Drawing(
            native_imports.DRAWING_TYPE_IMAGE,
            cast(pointer(self.drawing_image), c_void_p)
        )
