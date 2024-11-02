import inspect
import io
import logging
from typing import Dict, List, Optional, Sequence, Text, Tuple

import pygame
from pygame.event import Event

from pysaurus.core.prettylogging import PrettyLogging
from videre.core.clipboard import Clipboard
from videre.core.constants import MouseButton
from videre.core.events import MotionEvent
from videre.core.pygame_font_factory import PygameFontFactory
from videre.core.pygame_utils import PygameUtils
from videre.widgets.button import Button
from videre.widgets.widget import Widget
from videre.windowing.fancybox import Fancybox
from videre.windowing.windowlayout import WindowLayout
from videre.windowing.windowutils import on_event


class Window(PygameUtils, Clipboard):
    def __init__(self, title="Window", width=1280, height=720):
        super().__init__()
        self._title = str(title) or "Window"
        self._width = width
        self._height = height

        self._step_mode = False
        self._running = True
        self._closed = False
        self._screen: Optional[pygame.Surface] = None

        self._event_callbacks = {}
        self._down: Dict[MouseButton, Optional[Widget]] = {
            button: None for button in MouseButton
        }
        self._motion: Optional[Widget] = None
        self._manual_events: List[Event] = []
        self._layout: Optional[WindowLayout] = None
        self._fancybox: Optional[Fancybox] = None

        self._controls: List[Widget] = []
        self._fonts = PygameFontFactory()

        self.__collect_event_callbacks()

    def __repr__(self):
        return f"[{type(self).__name__}][{id(self)}]"

    fonts = property(lambda self: self._fonts)

    @property
    def controls(self) -> Tuple[Widget, ...]:
        return tuple(self._controls)

    @controls.setter
    def controls(self, controls: Sequence[Widget]):
        self._controls = controls

    def __enter__(self):
        if self._closed:
            raise RuntimeError("Window has already run. Cannot run again.")
        self._step_mode = True
        self._init_display()
        return self

    def render(self):
        assert self._step_mode
        for event in pygame.event.get():
            self.__on_event(event)
        self._render()

    def screenshot(self) -> io.BytesIO:
        assert self._step_mode
        data = io.BytesIO()
        pygame.image.save(self._screen, data)
        data.flush()
        return data

    def snapshot(self) -> io.BytesIO:
        self.render()
        return self.screenshot()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._step_mode:
            self._step_mode = False
            self._closed = True
            pygame.quit()

    def run(self):
        if self._closed:
            raise RuntimeError("Window has already run. Cannot run again.")
        if self._step_mode:
            raise RuntimeError("Window is in step mode. Cannot launch run().")

        self._init_display()
        # We must prepare initial events before entering the render loop
        self._register_initial_events()

        clock = pygame.time.Clock()
        while self._running:
            for event in pygame.event.get():
                self.__on_event(event)
            self._render()
            clock.tick(60)
        pygame.quit()
        self._closed = True

    def _init_display(self):
        self._screen = pygame.display.set_mode(
            (self._width, self._height), flags=pygame.RESIZABLE
        )
        pygame.display.set_caption(self._title)
        self._layout = WindowLayout(self._screen)

        # NB: As set_mode has been called, we can now initialize pygame.scrap.
        # This needs to be done before calling Clipboard methods.
        pygame.scrap.init()

    def _register_initial_events(self):
        # Post an initial mouse motion if mouse is over the window.
        if pygame.mouse.get_focused():
            self._post_manual_event(
                Event(
                    pygame.MOUSEMOTION,
                    pos=pygame.mouse.get_pos(),
                    rel=(0, 0),
                    buttons=(0, 0, 0),
                    touch=False,
                ),
                unique=True,
            )

    def _post_manual_event(self, event, unique=False):
        if not unique or event not in self._manual_events:
            self._manual_events.append(event)

    def _render(self):
        self._layout.controls = self.controls + (
            (self._fancybox,) if self._fancybox else ()
        )
        self._layout.render(self)
        pygame.display.flip()

        # Post manual events.
        if self._manual_events:
            for event in self._manual_events:
                pygame.event.post(event)
            self._manual_events.clear()

    def set_fancybox(
        self,
        content: Widget,
        title: str | Text = "Fancybox",
        buttons: Sequence[Button] = (),
        expand_buttons=True,
    ):
        assert not self._fancybox
        self._fancybox = Fancybox(content, title, buttons, expand_buttons)
        self._register_initial_events()

    def clear_fancybox(self):
        self._fancybox = None
        self._register_initial_events()

    def has_fancybox(self) -> bool:
        return self._fancybox is not None

    def __collect_event_callbacks(self):
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, "event_type"):
                event_type = method.event_type
                assert event_type not in self._event_callbacks
                self._event_callbacks[event_type] = method
        PrettyLogging.debug(
            {
                pygame.event.event_name(t): c.__name__
                for t, c in self._event_callbacks.items()
            }
        )

    def __on_event(self, event: Event):
        callback = self._event_callbacks.get(event.type)
        if callback is None:
            logging.debug(
                f"Unhandled pygame event: {pygame.event.event_name(event.type)}"
            )
            return False
        callback(event)
        return True

    @on_event(pygame.QUIT)
    def _on_quit(self, event: Event):
        print("Quit pygame.")
        self._running = False

    @on_event(pygame.MOUSEWHEEL)
    def _on_mouse_wheel(self, event: Event):
        owner = self._layout.get_mouse_wheel_owner(*pygame.mouse.get_pos())
        if owner:
            shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
            owner.widget.handle_mouse_wheel(event.x, event.y, shift)

    @on_event(pygame.MOUSEBUTTONDOWN)
    def _on_mouse_button_down(self, event: Event):
        owner = self._layout.get_mouse_owner(*event.pos)
        if owner:
            button = MouseButton(event.button)
            self._down[button] = owner.widget
            owner.widget.handle_mouse_down(button, owner.rel_x, owner.rel_y)

    @on_event(pygame.MOUSEBUTTONUP)
    def _on_mouse_button_up(self, event: Event):
        button = MouseButton(event.button)
        owner = self._layout.get_mouse_owner(*event.pos)
        if owner:
            owner.widget.handle_mouse_up(button, owner.rel_x, owner.rel_y)
            if self._down[button] == owner.widget:
                owner.widget.handle_click(button)
            elif self._down[button]:
                self._down[button].handle_mouse_down_canceled(button)
        elif self._down[button]:
            self._down[button].handle_mouse_down_canceled(button)
        self._down[button] = None

    @on_event(pygame.MOUSEMOTION)
    def _on_mouse_motion(self, event: Event):
        m_event = MotionEvent(event)
        owner = self._layout.get_mouse_owner(*event.pos)
        if owner:
            m_event = MotionEvent(event, owner.rel_x, owner.rel_y)
            if not self._motion:
                owner.widget.handle_mouse_enter(m_event)
            elif self._motion is owner.widget:
                owner.widget.handle_mouse_over(m_event)
            else:
                self._motion.handle_mouse_exit()
                owner.widget.handle_mouse_enter(m_event)
            self._motion = owner.widget
        elif self._motion:
            self._motion.handle_mouse_exit()
            self._motion = None
        for button in m_event.buttons:
            if self._down[button]:
                down = self._down[button]
                parent_x = 0 if down.parent is None else down.parent.global_x
                parent_y = 0 if down.parent is None else down.parent.global_y
                self._down[button].handle_mouse_down_move(
                    MotionEvent(event, event.pos[0] - parent_x, event.pos[1] - parent_y)
                )

    @on_event(pygame.WINDOWLEAVE)
    def _on_window_leave(self, event: Event):
        if self._motion:
            self._motion.handle_mouse_exit()
            self._motion = None

    @on_event(pygame.WINDOWRESIZED)
    def _on_window_resized(self, event: Event):
        print("Window resized:", event)
