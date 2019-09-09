from ctypes import c_void_p, Structure, POINTER, c_char_p, c_uint, c_bool, c_int, c_float

from pysaurus.core.meta.native import CLibrary


class Window(Structure):
    _fields_ = [
        ('handle', c_void_p)
    ]


class Event(Structure):
    _fields_ = [
        ('handle', c_void_p)
    ]


class Drawing(Structure):
    _fields_ = [
        ('type', c_int),
        ('drawing', c_void_p)
    ]


class DrawingImage(Structure):
    _fields_ = [
        ('path', c_char_p),
        ('x', c_float),
        ('y', c_float)
    ]


WindowPtr = POINTER(Window)
EventPtr = POINTER(Event)
DrawingPtr = POINTER(Drawing)
DrawingPtrPtr = POINTER(DrawingPtr)

_gui_raptor = CLibrary('guiRaptor')

WindowNew = _gui_raptor.prototype('WindowNew', WindowPtr, [c_uint, c_uint, c_char_p])
WindowDelete = _gui_raptor.prototype('WindowDelete', None, [WindowPtr])
WindowIsOpen = _gui_raptor.prototype('WindowIsOpen', c_bool, [WindowPtr])
WindowNextEvent = _gui_raptor.prototype('WindowNextEvent', c_bool, [WindowPtr, EventPtr])
WindowClose = _gui_raptor.prototype('WindowClose', None, [WindowPtr])
WindowDraw = _gui_raptor.prototype('WindowDraw', None, [WindowPtr, DrawingPtrPtr, c_uint])
EventNew = _gui_raptor.prototype('EventNew', EventPtr, None)
EventDelete = _gui_raptor.prototype('EventDelete', None, [EventPtr])
EventClosed = _gui_raptor.prototype('EventClosed', c_bool, [EventPtr])

DRAWING_TYPE_IMAGE = 0
