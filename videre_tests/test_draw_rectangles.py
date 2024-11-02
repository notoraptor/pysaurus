import pytest

from videre import Colors, Container, Gradient
from videre.windowing.windowfactory import WindowLD


@pytest.mark.parametrize("vertical", [False, True])
def test_gradient(vertical, image_testing):
    with WindowLD() as window:
        window.controls = [
            Container(
                background_color=Gradient(
                    Colors.red, Colors.green, Colors.blue, vertical=vertical
                )
            )
        ]
        image_testing(window.snapshot())


def test_background(image_testing):
    with WindowLD() as window:
        window.controls = [Container(background_color="yellow")]
        image_testing(window.snapshot())
