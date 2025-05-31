import videre
from videre import Button, Column, ScrollView, Text
from videre.windowing.windowfactory import WindowLD
from videre_tests.common import FakeUser


def test_fancybox_rendering(image_testing):
    with WindowLD() as window:

        def fancy(*args):
            window.set_fancybox(
                ScrollView(Column([Text(f"Item {i + 1}") for i in range(10)])),
                buttons=[Button("yes"), Button("NO!")],
            )

        window.controls = [Button("Fancy!", on_click=fancy, square=True)]
        fancy()

        image_testing(window.snapshot())


def test_fancybox(window_testing):
    def _fancy(*args, **kwargs):
        window_testing.set_fancybox(videre.Text("I am at top!"), title="fancybox")

    bt_open_fancybox = videre.Button("click", on_click=_fancy)
    window_testing.controls = [videre.Text("Hwllo, world!"), bt_open_fancybox]
    window_testing.render()

    assert not window_testing.find(videre.Text, text="fancybox")
    assert not window_testing.find(videre.Text, text="I am at top!")
    assert not window_testing.find(videre.Button, text="✕")

    FakeUser.click(bt_open_fancybox)
    window_testing.render()

    (_,) = window_testing.find(videre.Text, text="fancybox")
    (_,) = window_testing.find(videre.Text, text="I am at top!")
    (bt_close_fancybox,) = window_testing.find(videre.Button, text="✕")

    FakeUser.click(bt_close_fancybox)
    window_testing.render()

    assert not window_testing.find(videre.Text, text="fancybox")
    assert not window_testing.find(videre.Text, text="I am at top!")
    assert not window_testing.find(videre.Button, text="✕")
