from ctypes import c_void_p, Structure, POINTER, c_char_p, c_uint, c_bool, c_int, c_float, c_size_t

from pysaurus.core.meta.native import CLibrary


FloatPtr = POINTER(c_float)


class Window(Structure):
    _fields_ = [
        ('handle', c_void_p)
    ]


class Event(Structure):
    _fields_ = [
        ('handle', c_void_p)
    ]


class Pattern(Structure):
    _fields_ = [
        ('type', c_int),
        ('drawing', c_void_p)
    ]


class PatternTextInfo(Structure):
    _fields_ = [
        ('length', c_size_t),
        ('width', c_float),
        ('height', c_float),
        ('left', c_float),
        ('top', c_float),
        ('coordinates', FloatPtr),
    ]


PatternPtr = POINTER(Pattern)
PatternTextInfoPtr = POINTER(PatternTextInfo)
PatternPtrPtr = POINTER(PatternPtr)


class PatternText(Structure):
    _fields_ = [
        ('x', c_float),
        ('y', c_float),
        ('font', c_char_p),
        ('content', c_char_p),
        ('size', c_uint),
        ('outline', c_float),
        ('color', c_char_p),
        ('outlineColor', c_char_p),
        ('bold', c_bool),
        ('italic', c_bool),
        ('underline', c_bool),
        ('strike', c_bool),
    ]


class PatternFrame(Structure):
    _fields_ = [
        ('x', c_float),
        ('y', c_float),
        ('width', c_uint),
        ('height', c_uint),
        ('count', c_uint),
        ('patterns', PatternPtrPtr),
    ]


class PatternImage(Structure):
    _fields_ = [
        ('x', c_float),
        ('y', c_float),
        ('width', c_int),
        ('height', c_int),
        ('src', c_char_p),
    ]


class PatternRectangle(Structure):
    _fields_ = [
        ('x', c_float),
        ('y', c_float),
        ('width', c_float),
        ('height', c_float),
        ('outline', c_float),
        ('color', c_char_p),
        ('outlineColor', c_char_p),
    ]


WindowPtr = POINTER(Window)
EventPtr = POINTER(Event)
PatternTextPtr = POINTER(PatternText)
PatternFramePtr = POINTER(PatternFrame)
PatternImagePtr = POINTER(PatternImage)
PatternRectanglePtr = POINTER(PatternRectangle)

_gui_raptor = CLibrary('guiRaptor')

WindowNew = _gui_raptor.prototype('WindowNew', WindowPtr, [c_uint, c_uint, c_char_p])
WindowDelete = _gui_raptor.prototype('WindowDelete', None, [WindowPtr])
WindowIsOpen = _gui_raptor.prototype('WindowIsOpen', c_bool, [WindowPtr])
WindowNextEvent = _gui_raptor.prototype('WindowNextEvent', c_bool, [WindowPtr, EventPtr])
WindowClose = _gui_raptor.prototype('WindowClose', None, [WindowPtr])
WindowDraw = _gui_raptor.prototype('WindowDraw', None, [WindowPtr, PatternPtrPtr, c_uint])
EventNew = _gui_raptor.prototype('EventNew', EventPtr, None)
EventDelete = _gui_raptor.prototype('EventDelete', None, [EventPtr])
EventClosed = _gui_raptor.prototype('EventClosed', c_bool, [EventPtr])
PatternTextInfoNew = _gui_raptor.prototype('PatternTextInfoNew', PatternTextInfoPtr, [PatternTextPtr])
PatternTextInfoDelete = _gui_raptor.prototype('PatternTextInfoDelete', None, [PatternTextInfoPtr])

DRAWING_TYPE_IMAGE = 0
DRAWING_TYPE_TEXT = 1
DRAWING_TYPE_RECTANGLE = 2
DRAWING_TYPE_CIRCLE = 3
DRAWING_TYPE_REGULAR_POLYGON = 4
DRAWING_TYPE_POLYGON = 5
DRAWING_TYPE_ELLIPSE = 6
DRAWING_TYPE_SURFACE = 7
NB_DRAWING_TYPE = 8
