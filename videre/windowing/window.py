import logging
from typing import Dict, List, Optional, Sequence, Tuple

import pygame
from pygame.event import Event

from pysaurus.core.functions import get_tagged_methods
from pysaurus.core.prettylogging import PrettyLogging
from videre.colors import ColorDef, Colors, parse_color
from videre.core.clipboard import Clipboard
from videre.core.constants import Alignment, MouseButton, WINDOW_FPS
from videre.core.events import KeyboardEntry, MouseEvent
from videre.core.fontfactory.pygame_font_factory import PygameFontFactory
from videre.core.fontfactory.pygame_text_rendering import PygameTextRendering
from videre.core.pygame_utils import PygameUtils
from videre.layouts.container import Container
from videre.widgets.button import Button
from videre.widgets.text import Text
from videre.widgets.widget import Widget
from videre.windowing.context import Context
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
        "_hide",
    )

    def __init__(
        self,
        title="Window",
        width=1280,
        height=720,
        background: ColorDef = None,
        font_size=14,
        hide=False,
    ):
        super().__init__()
        self._title = str(title) or "Window"
        self._width = width
        self._height = height
        self._hide = bool(hide)
        self._screen_background = parse_color(background or Colors.white)

        self._running = True
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
        PrettyLogging.pinfo(
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

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

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
        if not self._running:
            raise RuntimeError("Window has already run. Cannot run again.")

        self._init_display()
        # We must prepare initial events before entering the render loop
        self._register_initial_events()

        clock = pygame.time.Clock()
        while self._running:
            self._render()
            clock.tick(WINDOW_FPS)
        pygame.quit()

    def _init_display(self):
        flags = pygame.RESIZABLE
        if self._hide:
            flags |= pygame.HIDDEN
        self._screen = pygame.display.set_mode((self._width, self._height), flags=flags)
        pygame.display.set_caption(self._title)
        self._layout = WindowLayout(self._screen, background=self._screen_background)

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
        self._layout.controls = (
            self.controls
            + ((self._fancybox,) if self._fancybox else ())
            + ((self._context,) if self._context else ())
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
        # We register initial events as `after` events.
        # We need to render the fancybox before the events are processed,
        # so what fancybox can properly capture these events.
        self._register_initial_events()

    def clear_fancybox(self):
        self._fancybox = None
        # We register initial events as `before` events.
        # Since fancybox is not rendered anymore (juste removed from controls),
        # initial events can be immediately processed with remaining controls,
        # without waiting for the next render.
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

    def set_context(self, relative: Widget, control: Widget, x=0, y=0):
        self._context = Context(relative, control, x=x, y=y)
        # todo why not register initial events?

    def clear_context(self):
        self._context = None
        self._register_initial_events(before=True)

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
            # Handle mouse down
            button = MouseButton(event.button)
            self._down[button] = owner.widget
            EventPropagator.handle_mouse_down(
                owner.widget,
                MouseEvent(x=owner.x_in_parent, y=owner.y_in_parent, buttons=[button]),
            )
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
            EventPropagator.handle_mouse_up(
                owner.widget,
                MouseEvent(x=owner.x_in_parent, y=owner.y_in_parent, buttons=[button]),
            )
            if self._down[button] == owner.widget:
                EventPropagator.handle_click(owner.widget, button)
            elif self._down[button]:
                EventPropagator.handle_mouse_down_canceled(self._down[button], button)
        elif self._down[button]:
            EventPropagator.handle_mouse_down_canceled(self._down[button], button)
        self._down[button] = None

    @on_event(pygame.MOUSEMOTION)
    def _on_mouse_motion(self, event: Event):
        m_event = MouseEvent.from_mouse_motion(event)
        owner = self._layout.get_mouse_owner(*event.pos)
        if owner:
            m_event = MouseEvent.from_mouse_motion(
                event, owner.x_in_parent, owner.y_in_parent
            )
            if not self._motion:
                EventPropagator.handle_mouse_enter(owner.widget, m_event)
            elif self._motion is owner.widget:
                EventPropagator.handle_mouse_over(owner.widget, m_event)
            else:
                EventPropagator.manage_mouse_motion(event, owner, self._motion)
            self._motion = owner.widget
        elif self._motion:
            EventPropagator.handle_mouse_exit(self._motion)
            self._motion = None
        for button in m_event.buttons:
            if self._down[button]:
                down = self._down[button]
                parent_x = 0 if down.parent is None else down.parent.global_x
                parent_y = 0 if down.parent is None else down.parent.global_y
                EventPropagator.handle_mouse_down_move(
                    self._down[button],
                    MouseEvent.from_mouse_motion(
                        event, event.pos[0] - parent_x, event.pos[1] - parent_y
                    ),
                )

    @on_event(pygame.WINDOWLEAVE)
    def _on_window_leave(self, event: Event):
        if self._motion:
            EventPropagator.handle_mouse_exit(self._motion)
            self._motion = None

    @on_event(pygame.WINDOWRESIZED)
    def _on_window_resized(self, event: Event):
        logger.debug(f"Window resized: {event}")
        self._width, self._height = event.x, event.y

    @on_event(pygame.TEXTINPUT)
    def _on_text_input(self, event: Event):
        if self._focus:
            self._focus.handle_text_input(event.text)

    @on_event(pygame.KEYDOWN)
    def _on_keydown(self, event: Event):
        if self._focus:
            self._focus.handle_keydown(KeyboardEntry(event))
