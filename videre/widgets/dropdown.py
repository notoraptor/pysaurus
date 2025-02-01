from typing import Optional, Self

import pygame

from videre import MouseButton
from videre.core.events import MouseEvent
from videre.core.sides.border import Border
from videre.core.sides.padding import Padding
from videre.layouts.column import Column
from videre.layouts.container import Container
from videre.layouts.control_layout import ControlLayout
from videre.layouts.row import Row
from videre.widgets.abstract_button import AbstractButton
from videre.widgets.text import Text


class _CaptureColumn(Column):
    __slots__ = ()
    __wprops__ = {}
    __capture_mouse__ = True


class Dropdown(ControlLayout):
    __slots__ = ("_hover", "_down", "_context")
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
        )
        super().__init__(container, **kwargs)
        self.options = options
        self.index = 0
        self._hover = False
        self._down = False

        self._context: Optional[Column] = None

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
        options = tuple(options)
        assert options
        self._set_wprop("options", options)
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

    def handle_mouse_enter(self, event: MouseEvent):
        self._hover = True
        self._set_color()

    def handle_mouse_exit(self):
        self._hover = False
        self._set_color()

    def handle_mouse_down(self, event: MouseEvent):
        self._down = True
        self._set_color()

        if self._context:
            self._close_context()
        else:
            self._open_context()

    def handle_mouse_up(self, event: MouseEvent):
        return self.handle_mouse_down_canceled(event.button)

    def handle_mouse_down_canceled(self, button: MouseButton):
        self._down = False
        self._set_color()

    def handle_focus_in(self) -> Self:
        return self

    def handle_focus_out(self):
        self._close_context()

    def _open_context(self):
        container = self._control()
        padding = container.padding
        arror_width = (
            Text(self.ARROW_DOWN).render(self.get_window(), None, None).get_width()
        )
        space = padding.left + padding.right + arror_width
        self._context = _CaptureColumn(
            [
                Container(
                    Text(str(option)),
                    background_color="green",
                    padding=Padding(right=space),
                )
                for option in self.options
            ],
            expand_horizontal=True,
        )
        self.get_window().set_context(self, self._context)

    def _close_context(self):
        if self._context:
            self.get_window().clear_context()
            self._context = None

    def _set_color(self):
        if self._down:
            color = AbstractButton._COLOR_DOWN
        elif self._hover:
            color = AbstractButton._COLOR_HOVER
        else:
            color = AbstractButton._COLOR_DEFAULT
        self._control().background_color = color

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        text_width = max(
            (
                Text(str(option)).render(window, None, None).get_width()
                for option in self.options
            ),
            default=0,
        )
        container_width = (
            text_width + Text(self.ARROW_DOWN).render(window, None, None).get_width()
        )
        container = self._control()
        margin = container.border.margin() + container.padding
        container.width = container_width + margin.left + margin.right
        return super().draw(window, width, height)
