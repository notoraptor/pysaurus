import inspect
import logging
import pprint
from typing import List, Optional

import pygame
from pygame.event import Event

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

    def __on_event(self, event: Event):
        callback = self._event_callbacks.get(event.type)
        if callback is None:
            logging.debug(
                f"Unhandled pygame event: {pygame.event.event_name(event.type)}"
            )
            return False
        callback(event)
        return True

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

    @on_event(pygame.QUIT)
    def _on_quit(self, event: Event):
        print("Quit pygame.")
        self._running = False

    def _get_mouse_owner(self, event: Event) -> Optional[Widget]:
        owners = [ctrl.get_mouse_owner(*event.pos) for ctrl in self.controls]
        owners = [ctrl for ctrl in owners if ctrl]
        if owners:
            owner, = owners
            return owner
        return None

    @on_event(pygame.MOUSEBUTTONDOWN)
    def _on_mouse_button_down(self, event: Event):
        owner = self._get_mouse_owner(event)
        if owner:
            self._down = (owner, event.button)

    @on_event(pygame.MOUSEBUTTONUP)
    def _on_mouse_button_up(self, event: Event):
        owner = self._get_mouse_owner(event)
        if owner and self._down == (owner, event.button):
            print(owner, "clicked with button", event.button)
        self._down = ()
