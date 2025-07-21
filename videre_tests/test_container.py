import itertools

import pytest

import videre
from videre.core.sides.padding import Padding


@pytest.mark.parametrize("border_size", [1, 2, 3])
def test_simple_container(border_size, fake_win):
    fake_win.controls = [
        videre.Container(
            videre.Text("Hello World!"), border=videre.Border.all(border_size)
        )
    ]
    fake_win.check()


@pytest.mark.parametrize(
    "halign,valign", itertools.product(videre.Alignment, videre.Alignment)
)
def test_container_alignments(fake_win, halign, valign):
    fake_win.controls = [
        videre.Container(
            videre.Text("Hello, World!"),
            background_color="pink",
            border=videre.Border.all(2, videre.Colors.blue),
            horizontal_alignment=halign,
            vertical_alignment=valign,
        )
    ]
    fake_win.check()


@pytest.mark.parametrize("padding", [0, 10, 50])
def test_container_padding(fake_win, padding):
    fake_win.controls = [
        videre.Container(
            videre.Text("Hello, World!"),
            background_color="pink",
            border=videre.Border.all(2, videre.Colors.blue),
            padding=Padding.axis(padding),
            vertical_alignment=videre.Alignment.START,
            horizontal_alignment=videre.Alignment.CENTER,
        )
    ]
    fake_win.check()


def test_container_too_big_borders(fake_win):
    fake_win.controls = [
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
    fake_win.check()
