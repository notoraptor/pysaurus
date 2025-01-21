from videre import MouseButton
from videre.core.events import MotionEvent
from videre.core.sides.border import Border
from videre.core.sides.padding import Padding
from videre.layouts.container import Container
from videre.layouts.control_layout import ControlLayout
from videre.layouts.row import Row
from videre.widgets.abstract_button import AbstractButton
from videre.widgets.text import Text


class Dropdown(ControlLayout):
    __slots__ = ("_hover", "_down")
    __wprops__ = {"options", "index"}
    __capture_mouse__ = True
    ARROW_DOWN = "▼"

    def __init__(self, options=(), **kwargs):
        text = Text()
        arrow = Text(self.ARROW_DOWN)
        container = Container(
            Row([Container(text, weight=1), arrow]),
            border=Border.all(1),
            padding=Padding.axis(AbstractButton._PAD_X, AbstractButton._PAD_Y),
            width=102,
        )
        super().__init__(container, **kwargs)
        self.options = options
        self.index = 0
        self._hover = False
        self._down = False

        if self.options:
            text.text = str(self.selected)

    def _control(self) -> Container:
        (ctrl,) = self._controls()
        return ctrl

    @property
    def options(self) -> tuple:
        return self._get_wprop("options")

    @options.setter
    def options(self, options: list | tuple):
        self._set_wprop("options", tuple(options))
        self.index = 0

    @property
    def index(self) -> int:
        return self._get_wprop("index")

    @index.setter
    def index(self, index: int):
        self._set_wprop("index", min(max(0, index), len(self.options) - 1))

    @property
    def selected(self):
        return self.options[self.index]

    def handle_click(self, button: MouseButton):
        print("dropdown clicked")
        return True

    def handle_mouse_enter(self, event: MotionEvent):
        self._hover = True
        self._set_color()

    def handle_mouse_exit(self):
        self._hover = False
        self._set_color()

    def handle_mouse_down(self, button: MouseButton, x: int, y: int):
        self._down = True
        self._set_color()

    def handle_mouse_up(self, button: MouseButton, x: int, y: int):
        return self.handle_mouse_down_canceled(button)

    def handle_mouse_down_canceled(self, button: MouseButton):
        self._down = False
        self._set_color()

    def _set_color(self):
        if self._down:
            color = AbstractButton._COLOR_DOWN
        elif self._hover:
            color = AbstractButton._COLOR_HOVER
        else:
            color = AbstractButton._COLOR_DEFAULT
        self._control().background_color = color
