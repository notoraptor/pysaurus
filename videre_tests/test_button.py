from types import SimpleNamespace

import pygame
from pygame.event import Event

import videre


def test_button(snapwin):
    snapwin.controls = [videre.Button(text="Hello World!")]


class FakeUser:
    @classmethod
    def click(cls, button):
        x = button.global_x + button.rendered_width // 2
        y = button.global_y + button.rendered_height // 2
        event_data = {"pos": (x, y), "button": pygame.BUTTON_LEFT}
        pygame.event.post(Event(pygame.MOUSEBUTTONDOWN, event_data))
        pygame.event.post(Event(pygame.MOUSEBUTTONUP, event_data))


def test_click(window_testing):
    data = SimpleNamespace(value=100)

    def on_click(button):
        data.value += 100

    assert data.value == 100

    button = videre.Button(text="Hello World!", on_click=on_click)
    window_testing.controls = [button]
    window_testing.render()

    FakeUser.click(button)

    window_testing.render()
    assert data.value == 200
