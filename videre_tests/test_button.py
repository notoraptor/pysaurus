from types import SimpleNamespace

import videre
from videre_tests.common import FakeUser


def test_button(snapwin):
    snapwin.controls = [videre.Button(text="Hello World!")]


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
