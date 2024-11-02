import itertools

import pytest

import videre
from videre.core.sides.padding import Padding
from videre.windowing.windowfactory import WindowLD


@pytest.mark.parametrize(
    "halign,valign", itertools.product(videre.Alignment, videre.Alignment)
)
def test_container_alignments(image_testing, halign, valign):
    with WindowLD() as window:
        window.controls = [
            videre.Container(
                videre.Text("Hello, World!"),
                background_color="pink",
                border=videre.Border.all(2, videre.Colors.blue),
                horizontal_alignment=halign,
                vertical_alignment=valign,
            )
        ]
        image_testing(window.snapshot())


@pytest.mark.parametrize("padding", [0, 10, 50])
def test_container_padding(image_testing, padding):
    with WindowLD() as window:
        window.controls = [
            videre.Container(
                videre.Text("Hello, World!"),
                background_color="pink",
                border=videre.Border.all(2, videre.Colors.blue),
                padding=Padding.axis(padding),
                vertical_alignment=videre.Alignment.START,
                horizontal_alignment=videre.Alignment.CENTER,
            )
        ]
        image_testing(window.snapshot())


def test_container_too_big_borders(image_testing):
    with WindowLD() as window:
        window.controls = [
            videre.Container(
                videre.Text("Hello, World!"),
                background_color="yellow",
                border=videre.Border(
                    top=(100, videre.Colors.red),
                    left=(50, (1, 255, 2)),
                    bottom=(200, videre.Colors.cyan),
                    right=25,
                ),
                padding=Padding(top=385, left=100, bottom=20),
                vertical_alignment=videre.Alignment.END,
                horizontal_alignment=videre.Alignment.CENTER,
            )
        ]
        image_testing(window.snapshot())
