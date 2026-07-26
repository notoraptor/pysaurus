"""Tests for BoolValueWidget and the three-state bool flow in the dialog.

"Not set" is not a third value: the domain of a bool stays {False, True}, and
picking "not set" clears the property (deletes the row) instead of writing to
it -- exactly what the Clear button does.
"""

import pytest

from pysaurus.interface.kyuti.dialogs.video_properties_dialog import (
    VideoPropertiesDialog,
)
from pysaurus.interface.kyuti.widgets.bool_value_widget import BoolValueWidget
from pysaurus.properties.properties import PropType
from tests.mocks.mock_database import MockVideoPattern


@pytest.fixture
def bool_prop():
    return PropType(
        name="watched", type="bool", multiple=False, default=[False], enumeration=None
    )


def _video(properties: dict) -> MockVideoPattern:
    return MockVideoPattern(
        {
            "video_id": 1,
            "filename": "/videos/test.mp4",
            "file_size": 1024,
            "mtime": 1700000000.0,
            "duration": 60,
            "duration_time_base": 1,
            "height": 1080,
            "width": 1920,
            "meta_title": "Test Video",
            "found": True,
            "unreadable": False,
            "watched": False,
            "with_thumbnails": False,
            "video_codec": "h264",
            "video_codec_description": "H.264",
            "audio_codec": "aac",
            "channels": 2,
            "sample_rate": 44100,
            "audio_bit_rate": 128000,
            "container_format": "mp4",
            "frame_rate_num": 30,
            "frame_rate_den": 1,
            "date_entry_modified": "2024-01-15",
            "similarity_id": None,
            "properties": properties,
        }
    )


class TestBoolValueWidget:
    def test_offers_three_states_by_default(self, qtbot):
        widget = BoolValueWidget()
        qtbot.addWidget(widget)

        assert [state for state, _ in widget._buttons] == [None, False, True]
        assert widget.value() is None  # "not set" is the initial state

    def test_offers_two_states_without_undefined(self, qtbot):
        widget = BoolValueWidget(with_undefined=False)
        qtbot.addWidget(widget)

        assert [state for state, _ in widget._buttons] == [False, True]
        assert widget.value() is False

    @pytest.mark.parametrize("value", [None, False, True])
    def test_value_round_trips(self, qtbot, value):
        widget = BoolValueWidget()
        qtbot.addWidget(widget)

        widget.set_value(value)

        assert widget.value() is value

    def test_states_are_exclusive(self, qtbot):
        widget = BoolValueWidget()
        qtbot.addWidget(widget)

        widget.set_value(True)
        widget.set_value(False)

        checked = [state for state, button in widget._buttons if button.isChecked()]
        assert checked == [False]

    def test_unshowable_value_falls_back_to_first_state(self, qtbot):
        """A two-state widget cannot show "not set"; it must stay on a value."""
        widget = BoolValueWidget(with_undefined=False)
        qtbot.addWidget(widget)

        widget.set_value(None)

        assert widget.value() is False

    def test_set_value_does_not_emit_changed(self, qtbot):
        """Only user clicks count as changes, so callers need no loading guard."""
        widget = BoolValueWidget()
        qtbot.addWidget(widget)
        emitted = []
        widget.changed.connect(lambda: emitted.append(True))

        widget.set_value(True)

        assert emitted == []

    def test_clicking_emits_changed(self, qtbot):
        widget = BoolValueWidget()
        qtbot.addWidget(widget)

        with qtbot.waitSignal(widget.changed, timeout=1000):
            widget._buttons[2][1].click()  # "Yes"

        assert widget.value() is True


class TestBoolFlowInVideoPropertiesDialog:
    def test_undefined_property_shows_not_set(self, qtbot, bool_prop, mock_context):
        """The default (False) must not be shown as an explicit "No"."""
        dialog = VideoPropertiesDialog(_video({}), [bool_prop], mock_context)
        qtbot.addWidget(dialog)

        assert dialog._property_widgets["watched"].value() is None

    @pytest.mark.parametrize("stored", [True, False])
    def test_stored_value_is_shown(self, qtbot, bool_prop, mock_context, stored):
        dialog = VideoPropertiesDialog(
            _video({"watched": [stored]}), [bool_prop], mock_context
        )
        qtbot.addWidget(dialog)

        assert dialog._property_widgets["watched"].value() is stored

    def test_picking_not_set_clears_the_property(self, qtbot, bool_prop, mock_context):
        dialog = VideoPropertiesDialog(
            _video({"watched": [True]}), [bool_prop], mock_context
        )
        qtbot.addWidget(dialog)

        dialog._property_widgets["watched"]._buttons[0][1].click()  # "Not set"

        assert "watched" in dialog._cleared

    def test_picking_a_value_undoes_the_clear(self, qtbot, bool_prop, mock_context):
        dialog = VideoPropertiesDialog(
            _video({"watched": [True]}), [bool_prop], mock_context
        )
        qtbot.addWidget(dialog)
        widget = dialog._property_widgets["watched"]

        widget._buttons[0][1].click()  # "Not set"
        widget._buttons[1][1].click()  # "No"

        assert "watched" not in dialog._cleared
        assert "watched" in dialog._user_modified

    def test_clear_button_selects_not_set(self, qtbot, bool_prop, mock_context):
        dialog = VideoPropertiesDialog(
            _video({"watched": [True]}), [bool_prop], mock_context
        )
        qtbot.addWidget(dialog)

        dialog._on_clear_property("watched")

        assert dialog._property_widgets["watched"].value() is None

    def test_reset_button_restores_the_initial_state(
        self, qtbot, bool_prop, mock_context
    ):
        dialog = VideoPropertiesDialog(_video({}), [bool_prop], mock_context)
        qtbot.addWidget(dialog)
        widget = dialog._property_widgets["watched"]

        widget._buttons[2][1].click()  # "Yes"
        dialog._on_reset_property("watched")

        assert widget.value() is None  # back to undefined, not to the default

    def test_accept_writes_the_picked_value(self, qtbot, bool_prop, mock_context):
        dialog = VideoPropertiesDialog(_video({}), [bool_prop], mock_context)
        qtbot.addWidget(dialog)
        calls = []
        mock_context.set_video_properties = lambda vid, props: calls.append(
            (vid, props)
        )

        dialog._property_widgets["watched"]._buttons[2][1].click()  # "Yes"
        dialog._on_accept()

        assert calls == [(1, {"watched": [True]})]

    def test_accept_deletes_when_set_back_to_not_set(
        self, qtbot, bool_prop, mock_context
    ):
        dialog = VideoPropertiesDialog(
            _video({"watched": [True]}), [bool_prop], mock_context
        )
        qtbot.addWidget(dialog)
        calls = []
        mock_context.set_video_properties = lambda vid, props: calls.append(
            (vid, props)
        )

        dialog._property_widgets["watched"]._buttons[0][1].click()  # "Not set"
        dialog._on_accept()

        assert calls == [(1, {"watched": []})]

    def test_accept_writes_nothing_when_untouched(self, qtbot, bool_prop, mock_context):
        dialog = VideoPropertiesDialog(_video({}), [bool_prop], mock_context)
        qtbot.addWidget(dialog)
        calls = []
        mock_context.set_video_properties = lambda vid, props: calls.append(
            (vid, props)
        )

        dialog._on_accept()

        assert calls == []
