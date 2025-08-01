import videre
from videre import Button, Column, ScrollView, Text
from videre_tests.common import FakeUser


def test_fancybox_rendering(fake_win):
    def fancy(*args):
        fake_win.set_fancybox(
            ScrollView(Column([Text(f"Item {i + 1}") for i in range(10)])),
            buttons=[Button("yes"), Button("NO!")],
        )

    fake_win.controls = [Button("Fancy!", on_click=fancy, square=True)]
    fancy()

    fake_win.check()


def test_fancybox(fake_win):
    def _fancy(*args, **kwargs):
        fake_win.set_fancybox(videre.Text("I am at top!"), title="fancybox")

    bt_open_fancybox = videre.Button("click", on_click=_fancy)
    fake_win.controls = [videre.Text("Hwllo, world!"), bt_open_fancybox]
    fake_win.render()

    assert not fake_win.find(videre.Text, text="fancybox")
    assert not fake_win.find(videre.Text, text="I am at top!")
    assert not fake_win.find(videre.Button, text="✕")

    FakeUser.click(bt_open_fancybox)
    fake_win.render()

    (_,) = fake_win.find(videre.Text, text="fancybox")
    (_,) = fake_win.find(videre.Text, text="I am at top!")
    (bt_close_fancybox,) = fake_win.find(videre.Button, text="✕")

    FakeUser.click(bt_close_fancybox)
    fake_win.render()

    assert not fake_win.find(videre.Text, text="fancybox")
    assert not fake_win.find(videre.Text, text="I am at top!")
    assert not fake_win.find(videre.Button, text="✕")
