import itertools

import pytest

import videre
from pysaurus.core.constants import LOREM_IPSUM
from videre.windowing.windowfactory import WindowSD

NB_LINES = (0, 1, 2)
WRAP = list(videre.TextWrap)
ALIGN = list(videre.TextAlign)


@pytest.mark.parametrize("nb_lines,wrap", itertools.product(NB_LINES, WRAP))
def test_text(nb_lines, wrap, image_testing):
    lorem_ipsum = ("\n" * nb_lines) + LOREM_IPSUM
    with WindowSD(background=videre.Colors.yellow) as window:
        window.controls = [videre.Text(lorem_ipsum, wrap=wrap)]
        image_testing(window.snapshot())


@pytest.mark.parametrize(
    "align,wrap",
    itertools.product([al for al in ALIGN if al != videre.TextAlign.NONE], WRAP),
)
def test_text_wrap(align, wrap, image_testing):
    with WindowSD(background=videre.Colors.yellow) as window:
        window.controls = [videre.Text(LOREM_IPSUM, wrap=wrap, align=align)]
        image_testing(window.snapshot())


def test_text_color(image_testing):
    with WindowSD(background=videre.Colors.gray) as window:
        window.controls = [
            videre.Column(
                [
                    videre.Text("hello"),
                    videre.Text("world", color="red"),
                    videre.Text("how Are you?", size=30, color="#ffeeaa"),
                    videre.Text("hello world", color="cyan"),
                ]
            )
        ]
        image_testing(window.snapshot())


def test_text_strong(image_testing):
    with WindowSD() as window:
        window.controls = [
            videre.Column(
                [
                    videre.Text("hello world 1.", size=30),
                    videre.Text("hello world 2.", size=30, strong=True),
                    videre.Text("hello world 3.", size=30),
                ]
            )
        ]
        image_testing(window.snapshot())


def test_text_italic(image_testing):
    with WindowSD() as window:
        window.controls = [
            videre.Column(
                [
                    videre.Text("hello world 1.", size=30),
                    videre.Text("hello world 2.", size=30, italic=True),
                    videre.Text("hello world 3.", size=30),
                ]
            )
        ]
        image_testing(window.snapshot())


def test_text_underline(image_testing):
    with WindowSD() as window:
        window.controls = [
            videre.Column(
                [
                    videre.Text("hello world 1_.", size=30),
                    videre.Text("hello world 2_.", size=30, underline=True),
                    videre.Text("hello world 3_.", size=30),
                ]
            )
        ]
        image_testing(window.snapshot())


def test_text_underline_colored(image_testing):
    with WindowSD() as window:
        window.controls = [
            videre.Column(
                [
                    videre.Text("hello world 1_.", size=30),
                    videre.Text(
                        "hello world 2_.", size=30, underline=True, color="red"
                    ),
                    videre.Text("hello world 3_.", size=30),
                ]
            )
        ]
        image_testing(window.snapshot())


def test_text_styles(image_testing):
    with WindowSD() as window:
        window.controls = [
            videre.Column(
                [
                    videre.Text("hello world 1_.", size=30),
                    videre.Text(
                        "hello world 2_. How are you ? I hope you are fine ! "
                        "Thanks ! And you ?",
                        size=30,
                        strong=True,
                        italic=True,
                        underline=True,
                    ),
                    videre.Text(
                        "hello world 2_. How are you ? I hope you are fine ! "
                        "Thanks ! And you ?",
                        size=30,
                        strong=True,
                        italic=True,
                        underline=True,
                        wrap=videre.TextWrap.CHAR,
                    ),
                    videre.Text(
                        "hello world 2_. How are you ? I hope you are fine ! "
                        "Thanks ! And you ?",
                        size=30,
                        strong=True,
                        italic=True,
                        underline=True,
                        wrap=videre.TextWrap.WORD,
                    ),
                    videre.Text("hello world 3_.", size=30),
                ]
            )
        ]
        image_testing(window.snapshot())
