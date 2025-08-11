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
        return cls.click_at(x, y)

    @classmethod
    def click_at(cls, x: int, y: int, button=pygame.BUTTON_LEFT):
        """Click at specific coordinates"""
        event_data = {"pos": (x, y), "button": button}
        pygame.event.post(Event(pygame.MOUSEBUTTONDOWN, event_data))
        pygame.event.post(Event(pygame.MOUSEBUTTONUP, event_data))

    @classmethod
    def mouse_motion(
        cls, x: int, y: int, button_left=False, button_middle=False, button_right=False
    ):
        event_data = {
            "pos": (x, y),
            "rel": (0, 0),
            "touch": False,
            "buttons": (int(button_left), int(button_middle), int(button_right)),
        }
        pygame.event.post(Event(pygame.MOUSEMOTION, event_data))

    @classmethod
    def mouse_wheel(cls, x: int, y: int):
        event_data = {"x": x, "y": y}
        pygame.event.post(Event(pygame.MOUSEWHEEL, event_data))
