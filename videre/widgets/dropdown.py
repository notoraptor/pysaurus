from typing import Optional, Self

import pygame

from videre.core.events import MouseEvent
from videre.layouts.column import Column
from videre.layouts.container import Container
from videre.layouts.reactive_container import Reactive
from videre.layouts.row import Row
from videre.widgets.text import Text


class _CaptureColumn(Column):
    __slots__ = ()
    __wprops__ = {}
    __capture_mouse__ = True


class Dropdown(Reactive):
    __slots__ = ("_context",)
    __wprops__ = {"options", "index"}
    ARROW_DOWN = "▼"

    def __init__(self, options=(), **kwargs):
        text = Text()
        arrow = Text(self.ARROW_DOWN)
        super().__init__(Row([Container(text, weight=1), arrow]), **kwargs)
        self.options = options
        self.index = 0
        self._context: Optional[Column] = None

        if self.options:
            text.text = str(self.selected)

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

    def handle_mouse_down(self, event: MouseEvent):
        super().handle_mouse_down(event)

        if self._context:
            self._close_context()
        else:
            self._open_context()

    def handle_focus_in(self) -> Self:
        return self

    def handle_focus_out(self):
        self._close_context()

    def _open_context(self):
        window = self.get_window()
        width = self._compute_width(window, include_border=False)
        self._context = _CaptureColumn(
            [
                Container(Text(str(option)), background_color="green", width=width)
                for option in self.options
            ],
            expand_horizontal=True,
        )
        window.set_context(self, self._context)

    def _close_context(self):
        if self._context:
            self.get_window().clear_context()
            self._context = None

    def _compute_width(self, window, include_border=True) -> int:
        text_width = (
            max(
                (
                    Text(str(option)).render(window, None, None).get_width()
                    for option in self.options
                ),
                default=0,
            )
            + Text(self.ARROW_DOWN).render(window, None, None).get_width()
        )

        container = self._container()
        margin = container.padding
        if include_border:
            margin = margin + container.border.margin()
        return margin.left + text_width + margin.right

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        self._container().width = self._compute_width(window)
        return super().draw(window, width, height)
