import logging
from typing import Dict, List, Optional, Sequence, Tuple

import pygame
from pygame.event import Event

from pysaurus.core.functions import get_tagged_methods
from pysaurus.core.prettylogging import PrettyLogging
from videre.core.clipboard import Clipboard
from videre.core.constants import Alignment, MouseButton, WINDOW_FPS
from videre.core.events import KeyboardEntry, MotionEvent
from videre.core.fontfactory.pygame_font_factory import PygameFontFactory
from videre.core.fontfactory.pygame_text_rendering import PygameTextRendering
from videre.core.pygame_utils import PygameUtils
from videre.layouts.container import Container
from videre.widgets.button import Button
from videre.widgets.text import Text
from videre.widgets.widget import Widget
from videre.windowing.event_propagator import EventPropagator
from videre.windowing.fancybox import Fancybox
from videre.windowing.windowlayout import WindowLayout
from videre.windowing.windowutils import on_event

logger = logging.getLogger(__name__)


class Window(PygameUtils, Clipboard):
    __slots__ = (
        "_title",
        "_width",
        "_height",
        "_screen_background",
        "_running",
        "_closed",
        "_screen",
        "_down",
        "_motion",
        "_focus",
        "_manual_events_before",
        "_manual_events_after",
        "_layout",
        "_controls",
        "_fancybox",
        "_context",
        "_fonts",
        "_event_callbacks",
    )

    def __init__(
        self,
        title="Window",
        width=1280,
        height=720,
        background: pygame.Color | None = None,
        font_size=14,
    ):
        super().__init__()
        self._title = str(title) or "Window"
        self._width = width
        self._height = height
        self._screen_background = background

        self._running = True
        self._closed = False
        self._screen: Optional[pygame.Surface] = None

        self._down: Dict[MouseButton, Optional[Widget]] = {
            button: None for button in MouseButton
        }
        self._motion: Optional[Widget] = None
        self._focus: Optional[Widget] = None
        self._manual_events_before: List[Event] = []
        self._manual_events_after: List[Event] = []
        self._layout: Optional[WindowLayout] = None

        self._controls: List[Widget] = []
        self._fancybox: Optional[Fancybox] = None
        self._context = None

        self._fonts = PygameFontFactory(size=font_size)

        self._event_callbacks = get_tagged_methods(self, "event_type")
        PrettyLogging.debug(
            {
                pygame.event.event_name(t): c.__name__
                for t, c in self._event_callbacks.items()
            }
        )

    def __repr__(self):
        return f"[{type(self).__name__}][{id(self)}]"

    @property
    def fonts(self) -> PygameFontFactory:
        return self._fonts

    @property
    def controls(self) -> Tuple[Widget, ...]:
        return tuple(self._controls)

    @controls.setter
    def controls(self, controls: Sequence[Widget]):
        self._controls = controls

    def text_rendering(
        self,
        size: int = None,
        strong: bool = False,
        italic: bool = False,
        underline: bool = False,
        height_delta: int = None,
    ) -> PygameTextRendering:
        return PygameTextRendering(
            self.fonts,
            size=size,
            strong=strong,
            italic=italic,
            underline=underline,
            height_delta=height_delta,
        )

    def run(self):
        if self._closed:
            raise RuntimeError("Window has already run. Cannot run again.")

        self._init_display()
        # We must prepare initial events before entering the render loop
        self._register_initial_events()

        clock = pygame.time.Clock()
        while self._running:
            self._render()
            clock.tick(WINDOW_FPS)
        pygame.quit()
        self._closed = True

    def _init_display(self):
        self._screen = pygame.display.set_mode(
            (self._width, self._height), flags=pygame.RESIZABLE
        )
        pygame.display.set_caption(self._title)
        self._layout = WindowLayout(self._screen, background=self._screen_background)

        # NB: As set_mode has been called, we can now initialize pygame.scrap.
        # This needs to be done before calling Clipboard methods.
        pygame.scrap.init()

        # Initialize keyboard repeat.
        # NB: TEXTINPUT events already handle repeat,
        # but we still need manual initialization for KEYDOWN/KEYUP events.
        # I don't know how to get default delay and interval values for TEXTINPUT,
        # so I tried here to set empiric values so that key repeat
        # is the most like textinput repeat.
        pygame.key.set_repeat(500, 35)

    def _register_initial_events(self, before=False):
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
                before=before,
            )

    def _post_manual_event(self, event, unique=False, before=False):
        events_collection = (
            self._manual_events_before if before else self._manual_events_after
        )
        if not unique or event not in events_collection:
            events_collection.append(event)

    def _render(self):
        # Handle interface events.
        for event in pygame.event.get():
            self.__on_event(event)

        # Refresh controls.
        self.__refresh_controls()

        # Clear [pre-manual events -> updated controls] cycle.
        while self._manual_events_before:
            events = self._manual_events_before
            self._manual_events_before = []
            for event in events:
                self.__on_event(event)
            self.__refresh_controls()

        # Refresh screen.
        self._layout.render(self)
        pygame.display.flip()

        # Post manual events.
        if self._manual_events_after:
            for event in self._manual_events_after:
                pygame.event.post(event)
            self._manual_events_after.clear()

    def __refresh_controls(self):
        self._layout.controls = self.controls + (
            (self._fancybox,) if self._fancybox else ()
        )

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
        self._register_initial_events(before=True)

    def has_fancybox(self) -> bool:
        return self._fancybox is not None

    def alert(self, message: str | Text, title: str | Text = "Alert"):
        if isinstance(message, str):
            message = Text(message)
        self.set_fancybox(
            Container(
                message,
                horizontal_alignment=Alignment.CENTER,
                vertical_alignment=Alignment.CENTER,
            ),
            title,
        )

    def __on_event(self, event: Event):
        callback = self._event_callbacks.get(event.type)
        if callback is None:
            logger.debug(
                f"Unhandled pygame event: {pygame.event.event_name(event.type)}"
            )
            return False
        callback(event)
        return True

    @on_event(pygame.QUIT)
    def _on_quit(self, event: Event):
        logger.warning("Quit pygame.")
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
            # Handle focus
            focus = EventPropagator.handle_focus_in(owner.widget)
            if self._focus and self._focus != focus:
                self._focus.handle_focus_out()
            self._focus = focus

    @on_event(pygame.MOUSEBUTTONUP)
    def _on_mouse_button_up(self, event: Event):
        button = MouseButton(event.button)
        owner = self._layout.get_mouse_owner(*event.pos)
        if owner:
            owner.widget.handle_mouse_up(button, owner.rel_x, owner.rel_y)
            if self._down[button] == owner.widget:
                EventPropagator.handle_click(owner.widget, button)
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
        logger.debug(f"Window resized: {event}")

    @on_event(pygame.TEXTINPUT)
    def _on_text_input(self, event: Event):
        if self._focus:
            self._focus.handle_text_input(event.text)

    @on_event(pygame.KEYDOWN)
    def _on_keydown(self, event: Event):
        if self._focus:
            self._focus.handle_keydown(KeyboardEntry(event))
