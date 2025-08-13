import videre
from videre_tests.common import FakeUser


def test_button(snap_win):
    snap_win.controls = [videre.Button(text="Hello World!")]


def test_click(fake_win):
    def on_click(button):
        button.text = "Hello Again!"

    button = videre.Button(text="Hello World!", on_click=on_click)
    assert button.on_click == on_click
    fake_win.controls = [button]
    fake_win.check("hello")

    FakeUser.click(button)

    fake_win.check("hello_again")
    assert button.text == "Hello Again!"
