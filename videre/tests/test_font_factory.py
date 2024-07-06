import functools

import pytest

from resource.fonts import FONT_NOTO_REGULAR
from videre.utils.pygame_font_factory import PygameFontFactory


@pytest.mark.parametrize("function_name", ("render_text", "render_text_wrap_words"))
def test_render_text(function_name):
    height_delta = 2
    ff = PygameFontFactory(size=24, overrides=[FONT_NOTO_REGULAR.path])
    line_height = ff.get_font(" ").get_sized_height(ff.size) + height_delta
    assert line_height == 35

    function = getattr(ff, function_name)
    ff_render_text = functools.partial(
        function, compact=True, height_delta=height_delta
    )

    s = ff_render_text("")
    assert s.get_width() == 0
    assert s.get_height() == 0

    s = ff_render_text("\v\b\t\r\0")
    assert s.get_width() == 0
    assert s.get_height() == 0

    s = ff_render_text("\n")
    assert s.get_width() == 0
    assert s.get_height() == line_height

    s = ff_render_text("\n\n\n")
    assert s.get_width() == 0
    assert s.get_height() == line_height * 3

    s = function("a", height_delta=height_delta, compact=False)
    assert s.get_width() == 12
    assert s.get_height() == line_height

    s = function("a\na", height_delta=height_delta, compact=False)
    assert s.get_width() == 12
    assert s.get_height() == line_height * 2

    s = function("a\na\na", height_delta=height_delta, compact=False)
    assert s.get_width() == 12
    assert s.get_height() == line_height * 3

    s = function("a\n\na", height_delta=height_delta, compact=False)
    assert s.get_width() == 12
    assert s.get_height() == line_height * 3

    s = function("a\n\na\n\n", height_delta=height_delta, compact=False)
    assert s.get_width() == 12
    assert s.get_height() == line_height * 5

    s = ff_render_text("a")
    assert s.get_width() == 12
    assert s.get_height() == 15

    s = ff_render_text("a\na")
    assert s.get_width() == 12
    assert s.get_height() == 15 + line_height

    s = ff_render_text("a\na\na")
    assert s.get_width() == 12
    assert s.get_height() == 15 + line_height * 2

    s = ff_render_text("a\n\na")
    assert s.get_width() == 12
    assert s.get_height() == 15 + line_height * 2

    s = ff_render_text("a\na\na\n\n")
    assert s.get_width() == 12
    assert s.get_height() == 15 + line_height * 4
