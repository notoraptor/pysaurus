import tkinter


class EventModifier:
    CONTROL = "Control"
    ALT = "Alt"
    SHIFT = "Shift"
    LOCK = "Lock"
    EXTENDED = "Extended"
    BUTTON1 = "Button1"
    BUTTON2 = "Button2"
    BUTTON3 = "Button3"
    BUTTON4 = "Button4"
    BUTTON5 = "Button5"
    COMMAND = "Command"
    OPTION = "Option"
    MOD3 = "Mod3"
    MOD4 = "Mod4"
    MOD5 = "Mod5"
    META = "Meta"
    DOUBLE = "Double"
    TRIPLE = "Triple"
    QUADRUPLE = "Quadruple"


class EventType:
    ACTIVATE = "Activate"
    BUTTON_PRESS = "ButtonPress"
    BUTTON_RELEASE = "ButtonRelease"
    CIRCULATE = "Circulate"
    CIRCULATE_REQUEST = "CirculateRequest"
    COLORMAP = "Colormap"
    CONFIGURE = "Configure"
    CONFIGURE_REQUEST = "ConfigureRequest"
    CREATE = "Create"
    DEACTIVATE = "Deactivate"
    DESTROY = "Destroy"
    ENTER = "Enter"
    EXPOSE = "Expose"
    FOCUS_IN = "FocusIn"
    FOCUS_OUT = "FocusOut"
    GRAVITY = "Gravity"
    KEY_PRESS = "KeyPress"
    KEY_RELEASE = "KeyRelease"
    LEAVE = "Leave"
    MAP = "Map"
    MAP_REQUEST = "MapRequest"
    MOTION = "Motion"
    MOUSE_WHEEL = "MouseWheel"
    PROPERTY = "Property"
    REPARENT = "Reparent"
    RESIZE_REQUEST = "ResizeRequest"
    UNMAP = "Unmap"
    VISIBILITY = "Visibility"


class _Event:
    __slots__ = ("_e",)

    def __init__(self, event: tkinter.Event):
        self._e = event

    def __repr__(self):
        name = type(self).__name__
        prop_names = sorted(
            key
            for key in dir(self)
            if isinstance(getattr(type(self), key, None), property)
        )
        return (
            f"{name}[{self.event_type}]"
            f"({', '.join(f'{key}={repr(getattr(self, key))}' for key in prop_names)})"
        )

    @property
    def event_type(self):
        return self._e.type.name

    @property
    def event_time(self):
        return self._e.time

    @property
    def x(self):
        return self._e.x

    @property
    def y(self):
        return self._e.y


class _MouseScreenMotionEvent(_Event):
    """
    ButtonPress, ButtonRelease, KeyPress, KeyRelease, Motion
    """

    @property
    def screen_x(self):
        return self._e.x_root

    @property
    def screen_y(self):
        return self._e.y_root


class KeyboardEvent(_MouseScreenMotionEvent):
    """
    KeyPress, KeyRelease
    """

    @property
    def key_code(self):
        return self._e.keycode

    @property
    def character(self):
        return self._e.char

    @property
    def keysym(self):
        return self._e.keysym


class MouseButtonEvent(_MouseScreenMotionEvent):
    """
    ButtonPress, ButtonRelease
    """

    @property
    def button_number(self):
        return self._e.num


class MouseMotionEvent(_MouseScreenMotionEvent):
    """Motion"""


class MouseEnterEvent(_Event):
    """Enter"""

    @property
    def window_has_focus(self):
        return self._e.focus


class MouseLeaveEvent(MouseEnterEvent):
    """Leave"""

    pass


class MouseWheelEvent(_Event):
    @property
    def delta(self):
        return self._e.delta


class WindowEvent(_Event):
    """
    Visibility, Unmap, Map, Expose, FocusIn, FocusOut, Circulate,
    Colormap, Gravity, Reparent, Property, Destroy, Activate,
    Deactivate
    """


class WindowChangeEvent(WindowEvent):
    """
    Configure, Expose
    """

    @property
    def window_width(self):
        return self._e.width

    @property
    def window_height(self):
        return self._e.height


class WindowVisibilityEvent(WindowEvent):
    """
    Visibility
    """

    @property
    def window_state(self):
        return self._e.state


_EVENT_TO_CLASS = {
    EventType.KEY_PRESS: KeyboardEvent,
    EventType.KEY_RELEASE: KeyboardEvent,
    EventType.BUTTON_PRESS: MouseButtonEvent,
    EventType.BUTTON_RELEASE: MouseButtonEvent,
    EventType.MOTION: MouseMotionEvent,
    EventType.ENTER: MouseEnterEvent,
    EventType.LEAVE: MouseLeaveEvent,
    EventType.MOUSE_WHEEL: MouseWheelEvent,
    EventType.VISIBILITY: WindowVisibilityEvent,
    EventType.UNMAP: WindowEvent,
    EventType.MAP: WindowEvent,
    EventType.FOCUS_IN: WindowEvent,
    EventType.FOCUS_OUT: WindowEvent,
    EventType.CIRCULATE: WindowEvent,
    EventType.COLORMAP: WindowEvent,
    EventType.GRAVITY: WindowEvent,
    EventType.REPARENT: WindowEvent,
    EventType.PROPERTY: WindowEvent,
    EventType.DESTROY: WindowEvent,
    EventType.ACTIVATE: WindowEvent,
    EventType.DEACTIVATE: WindowEvent,
    EventType.EXPOSE: WindowChangeEvent,
    EventType.CONFIGURE: WindowChangeEvent,
}


def my_event(e: tkinter.Event) -> _Event:
    name = e.type.name
    if name not in _EVENT_TO_CLASS:
        raise ValueError(f"Unhandled tkinter event: {name}")
    return _EVENT_TO_CLASS[name](e)
