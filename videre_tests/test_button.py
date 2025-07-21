from types import SimpleNamespace

import videre
from videre_tests.common import FakeUser


def test_button(snap_win):
    snap_win.controls = [videre.Button(text="Hello World!")]


def test_click(fake_win):
    data = SimpleNamespace(value=100)

    def on_click(button):
        data.value += 100

    assert data.value == 100

    button = videre.Button(text="Hello World!", on_click=on_click)
    fake_win.controls = [button]
    fake_win.render()

    FakeUser.click(button)

    fake_win.render()
    assert data.value == 200
