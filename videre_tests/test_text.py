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
