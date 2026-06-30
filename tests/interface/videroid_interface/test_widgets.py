"""Tests for videroid custom widgets (theme / table / tabs / video_card).

These are mostly backend-free: built and rendered in a headless StepWindow.
video_card needs a real VideoPattern, taken from the example database.
"""

import videre
from videre.colors import Color
from videre.testing.step_window import StepWindow

from pysaurus.interface.videroid import theme
from pysaurus.interface.videroid.widgets import table
from pysaurus.interface.videroid.widgets.tabs import Tabs
from pysaurus.interface.videroid.widgets.video_card import VideoCard
from tests.interface.videroid_interface._widget_tree import find as _find
from tests.interface.videroid_interface._widget_tree import texts as _texts


def _render(*widgets):
    with StepWindow() as win:
        win.controls = list(widgets)
        win.render()


class TestTheme:
    def test_colors_have_expected_rgb(self):
        assert isinstance(theme.HEADER_BG, Color)
        assert theme.HEADER_BG == videre.parse_color((225, 225, 225))
        assert theme.EVEN_BG == videre.parse_color((245, 245, 245))

    def test_badge_and_selected_unified(self):
        # The point-4 unification: a single value each, no drift.
        assert theme.BADGE_BG == videre.parse_color((240, 240, 240))
        assert theme.SELECTED_BG == videre.parse_color((227, 242, 253))


class TestTableHelpers:
    def test_cell_holds_styled_text(self):
        cell = table.cell("hello", weight=2, strong=True)
        assert cell.weight == 2
        (text,) = _find(cell, videre.Text)
        assert text.text == "hello" and text.strong is True

    def test_header_builds_one_cell_per_column(self):
        header = table.header([("Name", 2), ("Count", 1), ("Size", 2)])
        assert header.background_color == videre.Gradient.parse(theme.HEADER_BG)
        assert _texts(header) == ["Name", "Count", "Size"]
        assert all(t.strong for t in _find(header, videre.Text))  # header is bold
        _render(header)  # also paints without error


class TestTabs:
    def _tabs(self):
        return Tabs(
            [("Alpha", lambda: videre.Text("a")), ("Beta", lambda: videre.Text("b"))]
        )

    def test_starts_on_first_tab_content(self):
        tabs = self._tabs()
        assert tabs.active_index == 0
        assert tabs._holder.control.text == "a"  # first builder's content shown

    def test_switch_changes_active_and_content(self):
        tabs = self._tabs()
        tabs._on_click(type("Btn", (), {"data": 1})())
        assert tabs.active_index == 1
        assert tabs._holder.control.text == "b"  # second builder's content now

    def test_refresh_rebuilds_active_content(self):
        tabs = self._tabs()
        before = tabs._holder.control
        tabs.refresh()
        after = tabs._holder.control
        assert after is not before  # the builder ran again (fresh widget)
        assert after.text == "a"  # still the active (first) tab

    def test_fill_flag_sets_holder_weight(self):
        assert Tabs([("X", lambda: videre.Text("x"))], fill=True)._holder.weight == 1
        assert Tabs([("X", lambda: videre.Text("x"))], fill=False)._holder.weight == 0


class TestVideoCard:
    def test_shows_real_video_title(self, videroid_context_example):
        video = videroid_context_example.get_videos(100, 0).result[0]
        card = VideoCard(video, index=0)
        assert str(video.title) in _texts(card)
        _render(card)  # paints without error

    def test_selected_background(self, videroid_context_example):
        video = videroid_context_example.get_videos(100, 0).result[0]
        parse = videre.Gradient.parse  # Container stores background_color this way
        assert VideoCard(video, index=1, selected=True).background_color == parse(
            theme.SELECTED_BG
        )
        assert VideoCard(video, index=1, selected=False).background_color == parse(
            theme.EVEN_BG
        )
        # Unselected even-index card has no highlight (the default empty gradient).
        assert VideoCard(video, index=0, selected=False).background_color == parse(None)

    def test_card_with_properties_shows_badges(self, videroid_context_example):
        videos = videroid_context_example.get_videos(100, 0).result
        with_props = next((v for v in videos if v.properties), None)
        assert with_props is not None  # the example DB has tagged videos
        card = VideoCard(with_props, index=0)
        assert "PROPERTIES" in _texts(card)
        badge_bg = videre.Gradient.parse(theme.BADGE_BG)
        badges = [
            c for c in _find(card, videre.Container) if c.background_color == badge_bg
        ]
        assert badges  # at least one property value rendered as a badge
