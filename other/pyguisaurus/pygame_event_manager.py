"""
Unused
"""
import sys
from typing import Any

import pygame
import pygame.event


class PyGameEventManager:
    def __init__(self):
        self._callbacks = {}

    def register(self, event_type, callback):
        assert pygame.NOEVENT < event_type < pygame.NUMEVENTS
        self._callbacks[event_type] = callback

    def unregister(self, event_type: int):
        self._callbacks.pop(event_type, None)

    def manage(self, event: pygame.event.Event, data: Any) -> bool:
        if event.type in self._callbacks:
            callback = self._callbacks[event.type]
            callback(event, data)
            return True
        else:
            print(
                f"Unhandled pygame event:",
                pygame.event.event_name(event.type),
                file=sys.stderr,
            )
            return False
