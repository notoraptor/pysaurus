import inspect
import logging
import pprint
from typing import List, Optional

import pygame
from pygame.event import Event

from other.pyguisaurus.enumerations import MouseButton
from other.pyguisaurus.events import MotionEvent
from other.pyguisaurus.utils import get_top_mouse_owner, get_top_mouse_wheel_owner
from other.pyguisaurus.widget import Widget


def on_event(event_type: int):
    def decorator(function):
        function.event_type = event_type
        return function

    return decorator


class Window:
    def __init__(self, title="Window", width=1280, height=720):
        self.title = title
        self.width = width
        self.height = height
        self.surfaces = []
        self.controls: List[Widget] = []
        self._running = True
        self._event_callbacks = {}
        self._down = ()
        self._motion: Optional[Widget] = None

        self.__collect_event_callbacks()

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
        pygame.display.set_caption(self.title)
        clock = pygame.time.Clock()

        while self._running:
            for event in pygame.event.get():
                self.__on_event(event)
            screen_width, screen_height = screen.get_width(), screen.get_height()
            screen.fill("white")
            for control in self.controls:
                surface = control.render(self, screen_width, screen_height)
                screen.blit(surface, (control.x, control.y))
            for surface in self.surfaces:
                screen.blit(surface, (0, 0))
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()

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

    @on_event(pygame.MOUSEMOTION)
    def _on_mouse_motion(self, event: Event):
        # print(event.pos, event.rel, event.buttons)
        owner = get_top_mouse_owner(*event.pos, self.controls)
        if owner:
            m_event = MotionEvent(event)
            if not self._motion:
                owner.handle_mouse_enter(m_event)
            elif self._motion is owner:
                owner.handle_mouse_over(m_event)
            else:
                self._motion.handle_mouse_exit(m_event)
                owner.handle_mouse_enter(m_event)
            self._motion = owner

    @on_event(pygame.MOUSEBUTTONDOWN)
    def _on_mouse_button_down(self, event: Event):
        owner = get_top_mouse_owner(*event.pos, self.controls)
        if owner:
            self._down = (owner, event.button)
            owner.handle_mouse_down(MouseButton(event.button), *event.pos)

    @on_event(pygame.MOUSEBUTTONUP)
    def _on_mouse_button_up(self, event: Event):
        owner = get_top_mouse_owner(*event.pos, self.controls)
        if owner:
            button = MouseButton(event.button)
            owner.handle_mouse_up(button, *event.pos)
            if self._down == (owner, event.button):
                # print(owner, "click", button)
                owner.handle_click(button)
        self._down = ()

    @on_event(pygame.MOUSEWHEEL)
    def _on_mouse_wheel(self, event: Event):
        owner = get_top_mouse_wheel_owner(*pygame.mouse.get_pos(), self.controls)
        if owner:
            shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
            # print(owner, event.x, event.y, shift)
            owner.handle_mouse_wheel(event.x, event.y, shift)
