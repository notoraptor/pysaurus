import inspect
import logging
import pprint
from typing import Dict, List, Optional

import pygame
from pygame.event import Event

from resource.fonts import FONT_NOTO_REGULAR
from videre.colors import Colors
from videre.core.events import MotionEvent, MouseButton
from videre.core.pygame_font_factory import PygameFontFactory
from videre.core.pygame_utils import PygameUtils
from videre.layouts.abstractlayout import AbstractControlsLayout
from videre.widgets.widget import Widget


def on_event(event_type: int):
    def decorator(function):
        function.event_type = event_type
        return function

    return decorator


class WindowLayout(AbstractControlsLayout):
    __slots__ = ()
    _FILL = Colors.white

    def __init__(self, screen: pygame.Surface):
        super().__init__()
        self._surface = screen

    def render(self, window, width: int = None, height: int = None) -> pygame.Surface:
        return super().render(
            window, self._surface.get_width(), self._surface.get_height()
        )

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        screen = self._surface

        screen_width, screen_height = screen.get_width(), screen.get_height()
        screen.fill(self._FILL)
        for control in self.controls:
            surface = control.render(window, screen_width, screen_height)
            screen.blit(surface, (control.x, control.y))

        return screen


class Window(PygameUtils):
    def __init__(self, title="Window", width=1280, height=720):
        super().__init__()
        self.title = title
        self.width = width
        self.height = height
        self.controls: List[Widget] = []
        self._running = True
        self._event_callbacks = {}
        self._down: Dict[MouseButton, Optional[Widget]] = {
            button: None for button in MouseButton
        }
        self._motion: Optional[Widget] = None
        self._layout: Optional[WindowLayout] = None

        self.fonts = PygameFontFactory(overrides=[FONT_NOTO_REGULAR.path])

        self.__collect_event_callbacks()

    def __repr__(self):
        return f"[{type(self).__name__}][{id(self)}]"

    def __collect_event_callbacks(self):
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, "event_type"):
                event_type = method.event_type
                assert event_type not in self._event_callbacks
                self._event_callbacks[event_type] = method

        pprint.pprint(
            {
                pygame.event.event_name(t): c.__name__
                for t, c in self._event_callbacks.items()
            }
        )

    def run(self):
        screen = pygame.display.set_mode(
            (self.width, self.height), flags=pygame.RESIZABLE
        )

        # NB: As set_mode has been called, we can now init pygame.scrap.
        pygame.scrap.init()

        pygame.display.set_caption(self.title)
        clock = pygame.time.Clock()

        self._layout = WindowLayout(screen)
        self._render()
        if pygame.mouse.get_focused():
            pygame.event.post(
                Event(
                    pygame.MOUSEMOTION,
                    pos=pygame.mouse.get_pos(),
                    rel=(0, 0),
                    buttons=(0, 0, 0),
                    touch=False,
                )
            )

        while self._running:
            for event in pygame.event.get():
                self.__on_event(event)
            self._render()
            clock.tick(60)
        pygame.quit()

    def _render(self):
        self._layout.controls = self.controls
        self._layout.render(self)
        pygame.display.flip()

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
