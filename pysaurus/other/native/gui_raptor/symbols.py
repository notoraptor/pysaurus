from ctypes import (
    POINTER,
    Structure,
    c_bool,
    c_char_p,
    c_float,
    c_int,
    c_size_t,
    c_uint,
    c_void_p,
)

from pysaurus.core.clibrary import CLibrary

FloatPtr = POINTER(c_float)


class Event(Structure):
    _fields_ = [("handle", c_void_p)]


class Pattern(Structure):
    _fields_ = [("type", c_int), ("drawing", c_void_p)]


class PatternTextInfo(Structure):
    _fields_ = [
        ("length", c_size_t),
        ("width", c_float),
        ("height", c_float),
        ("left", c_float),
        ("top", c_float),
        ("coordinates", FloatPtr),
    ]


PatternPtr = POINTER(Pattern)
PatternPtrPtr = POINTER(PatternPtr)


class NoPattern(Structure):
    _fields_ = []


class PatternText(Structure):
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
        ("font", c_char_p),
        ("content", c_char_p),
        ("size", c_uint),
        ("outline", c_float),
        ("color", c_char_p),
        ("outlineColor", c_char_p),
        ("bold", c_bool),
        ("italic", c_bool),
        ("underline", c_bool),
        ("strike", c_bool),
    ]


class PatternFrame(Structure):
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
        ("width", c_uint),
        ("height", c_uint),
        ("count", c_uint),
        ("patterns", PatternPtrPtr),
    ]


class PatternImage(Structure):
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
        ("width", c_float),
        ("height", c_float),
        ("src", c_char_p),
    ]


class PatternRectangle(Structure):
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
        ("width", c_float),
        ("height", c_float),
        ("outline", c_float),
        ("color", c_char_p),
        ("outlineColor", c_char_p),
    ]


EventPtr = POINTER(Event)
PatternTextPtr = POINTER(PatternText)
PatternFramePtr = POINTER(PatternFrame)
PatternImagePtr = POINTER(PatternImage)
PatternRectanglePtr = POINTER(PatternRectangle)
PatternTextInfoPtr = POINTER(PatternTextInfo)

_lib = CLibrary("guiRaptor")

WindowNew = _lib.prototype("WindowNew", c_void_p, [c_uint, c_uint, c_char_p])
WindowDelete = _lib.prototype("WindowDelete", None, [c_void_p])
WindowIsOpen = _lib.prototype("WindowIsOpen", c_bool, [c_void_p])
WindowNextEvent = _lib.prototype("WindowNextEvent", c_bool, [c_void_p, EventPtr])
WindowClose = _lib.prototype("WindowClose", None, [c_void_p])
WindowDraw = _lib.prototype("WindowDraw", None, [c_void_p, PatternPtrPtr, c_uint])
EventNew = _lib.prototype("EventNew", EventPtr, None)
EventDelete = _lib.prototype("EventDelete", None, [EventPtr])
EventClosed = _lib.prototype("EventClosed", c_bool, [EventPtr])
PatternTextInfoNew = _lib.prototype(
    "PatternTextInfoNew", PatternTextInfoPtr, [PatternTextPtr]
)
PatternTextInfoDelete = _lib.prototype(
    "PatternTextInfoDelete", None, [PatternTextInfoPtr]
)

DRAWING_TYPE_IMAGE = 0
DRAWING_TYPE_TEXT = 1
DRAWING_TYPE_RECTANGLE = 2
DRAWING_TYPE_CIRCLE = 3
DRAWING_TYPE_REGULAR_POLYGON = 4
DRAWING_TYPE_POLYGON = 5
DRAWING_TYPE_ELLIPSE = 6
DRAWING_TYPE_SURFACE = 7
NB_DRAWING_TYPE = 8
