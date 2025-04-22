import os

import pygame
from pygame.event import Event

from videre.widgets.widget import Widget

IMAGE_EXAMPLE = os.path.join(os.path.dirname(__file__), "flowers-7660120_640.jpg")
assert os.path.isfile(IMAGE_EXAMPLE)


class FakeUser:
    @classmethod
    def click(cls, button: Widget):
        x = button.global_x + button.rendered_width // 2
        y = button.global_y + button.rendered_height // 2
        event_data = {"pos": (x, y), "button": pygame.BUTTON_LEFT}
        pygame.event.post(Event(pygame.MOUSEBUTTONDOWN, event_data))
        pygame.event.post(Event(pygame.MOUSEBUTTONUP, event_data))
