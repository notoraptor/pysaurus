"""Coverage for VideoPropertiesDialog: every editor kind, the diff semantics of
get_changes ({} untouched, [value] set, [] delete, invalid input ignored), and
the read-only Info tab. Videos are MockVideoPattern; no window needed."""

import videre

from pysaurus.interface.videroid.dialogs.video_properties_dialog import (
    _NO_VALUE,
    VideoPropertiesDialog,
)
from pysaurus.properties.properties import PropType
from tests.interface.videroid_interface._widget_tree import find as _find
from tests.interface.videroid_interface._widget_tree import texts as _texts
from tests.mocks.mock_database import MockVideoPattern

_BASE = {"filename": "/v.mp4", "file_size": 1024, "video_id": 1, "mtime": 0.0}


def _prop(name, type="str", multiple=False, enumeration=None):
    return PropType(
        name=name, type=type, multiple=multiple, default=[], enumeration=enumeration
    )


def _video(properties=None, **overrides):
    data = dict(_BASE, properties=properties or {}, **overrides)
    return MockVideoPattern(data)


class TestSingleText:
    def test_defined_loads_and_untouched_is_no_change(self):
        dialog = VideoPropertiesDialog(_video({"note": ["hello"]}), [_prop("note")])
        record = dialog._editors["note"]
        assert record["widget"].value == "hello"
        assert dialog.get_changes() == {}

    def test_edit_sets_and_blank_deletes(self):
        dialog = VideoPropertiesDialog(_video({"note": ["hello"]}), [_prop("note")])
        dialog._editors["note"]["widget"].value = "world"
        assert dialog.get_changes() == {"note": ["world"]}
        dialog._editors["note"]["widget"].value = "  "  # blank -> delete
        assert dialog.get_changes() == {"note": []}

    def test_undefined_blank_is_no_change_and_typed_sets(self):
        dialog = VideoPropertiesDialog(_video(), [_prop("note")])
        assert dialog._editors["note"]["widget"].value == ""  # loads empty
        assert dialog.get_changes() == {}
        dialog._editors["note"]["widget"].value = "x"
        assert dialog.get_changes() == {"note": ["x"]}

    def test_int_parses_and_invalid_is_ignored(self):
        dialog = VideoPropertiesDialog(_video({"n": [3]}), [_prop("n", type="int")])
        widget = dialog._editors["n"]["widget"]
        widget.value = "7"
        assert dialog.get_changes() == {"n": [7]}
        widget.value = "abc"  # unparseable -> keep initial (kyuti skips it)
        assert dialog.get_changes() == {}

    def test_float_parses(self):
        dialog = VideoPropertiesDialog(_video(), [_prop("f", type="float")])
        dialog._editors["f"]["widget"].value = "2.5"
        assert dialog.get_changes() == {"f": [2.5]}


class TestSingleChoice:
    def test_enum_defined_selects_value_and_sentinel_deletes(self):
        prop = _prop("cat", enumeration=["a", "b"])
        dialog = VideoPropertiesDialog(_video({"cat": ["b"]}), [prop])
        widget = dialog._editors["cat"]["widget"]
        assert widget.selected == "b"
        assert dialog.get_changes() == {}
        widget.index = 1  # "a"
        assert dialog.get_changes() == {"cat": ["a"]}
        widget.index = 0  # "(no value)" sentinel -> delete
        assert widget.selected == _NO_VALUE
        assert dialog.get_changes() == {"cat": []}

    def test_enum_undefined_loads_sentinel(self):
        prop = _prop("cat", enumeration=["a", "b"])
        dialog = VideoPropertiesDialog(_video(), [prop])
        assert dialog._editors["cat"]["widget"].selected == _NO_VALUE
        assert dialog.get_changes() == {}

    def test_bool_maps_true_false(self):
        dialog = VideoPropertiesDialog(
            _video({"seen": [True]}), [_prop("seen", type="bool")]
        )
        widget = dialog._editors["seen"]["widget"]
        assert widget.selected == "true"  # loaded from stored True
        widget.index = 2  # "false"
        assert dialog.get_changes() == {"seen": [False]}


class TestMultiEnum:
    def test_checks_follow_stored_and_diff_in_enum_order(self):
        prop = _prop("tags", multiple=True, enumeration=["x", "y", "z"])
        dialog = VideoPropertiesDialog(_video({"tags": ["z", "x"]}), [prop])
        checks = dict(dialog._editors["tags"]["checks"])
        assert checks["x"].checked and checks["z"].checked
        assert not checks["y"].checked
        assert dialog.get_changes() == {}  # initial normalized to enum order
        checks["y"].checked = True
        checks["x"].checked = False
        assert dialog.get_changes() == {"tags": ["y", "z"]}


class TestMultiList:
    def test_add_remove_clear_and_dedup(self):
        prop = _prop("tags", multiple=True)
        dialog = VideoPropertiesDialog(_video({"tags": ["a"]}), [prop])
        record = dialog._editors["tags"]
        record["input"].value = "b"
        dialog._add_value("tags")
        assert record["values"] == ["a", "b"]
        assert record["input"].value == ""  # input cleared after add
        record["input"].value = "a"  # duplicate -> ignored
        dialog._add_value("tags")
        assert record["values"] == ["a", "b"]
        assert dialog.get_changes() == {"tags": ["a", "b"]}
        dialog._remove_value("tags", "a")
        assert record["values"] == ["b"]
        dialog._clear_list("tags")
        assert record["values"] == []
        assert dialog.get_changes() == {"tags": []}  # delete-all

    def test_add_blank_ignored_and_invalid_shows_error(self):
        prop = _prop("nums", multiple=True, type="int")
        dialog = VideoPropertiesDialog(_video(), [prop])
        record = dialog._editors["nums"]
        record["input"].value = "   "
        dialog._add_value("nums")  # blank -> no-op, no error
        assert record["values"] == [] and record["error"].text == ""
        record["input"].value = "abc"
        dialog._add_value("nums")  # unparseable -> error message
        assert record["values"] == []
        assert "Invalid value for type int." == record["error"].text
        record["input"].value = "4"
        dialog._add_value("nums")  # a valid add clears the error
        assert record["values"] == [4] and record["error"].text == ""

    def test_list_renders_values_with_remove_buttons(self):
        prop = _prop("tags", multiple=True)
        dialog = VideoPropertiesDialog(_video({"tags": ["a", "b"]}), [prop])
        column = dialog._editors["tags"]["column"]
        assert "a" in _texts(column) and "b" in _texts(column)
        buttons = _find(column, videre.Button)
        assert len(buttons) == 2  # one ✕ per value
        buttons[0].on_click(buttons[0])  # remove "a" (invoke handler directly)
        assert dialog._editors["tags"]["values"] == ["b"]


class TestDialogShell:
    def test_no_prop_types_shows_placeholder(self):
        dialog = VideoPropertiesDialog(_video(), [])
        assert "No custom properties defined." in _texts(dialog)

    def test_sections_show_name_and_details(self):
        props = [_prop("note"), _prop("tags", multiple=True, enumeration=["x"])]
        dialog = VideoPropertiesDialog(_video(), props)
        texts = _texts(dialog)
        assert "note  (str)" in texts
        assert "tags  (str, multiple, enum)" in texts

    def test_info_tab_full_video(self):
        video = _video(
            meta_title="My Movie",
            date_entry_modified="2024-01-01",
            duration=90.0,
            width=1920,
            height=1080,
            video_codec="h264",
            video_codec_description="H.264",
            container_format="mp4",
            frame_rate_num=30,
            frame_rate_den=1,
            audio_codec="aac",
            channels=2,
            sample_rate=48000,
            audio_bit_rate=128000,
            audio_bit_rate_formatted="128 Kb",
            found=True,
            with_thumbnails=True,
            similarity_id=3,
            similarity_id_reencoded=5,
        )
        info = VideoPropertiesDialog(video, [])._build_info()
        texts = _texts(info)
        assert "My Movie" in texts and "h264" in texts
        assert "30.00 fps" in texts and "48000 Hz" in texts
        assert "128 Kb/s" in texts
        assert "3" in texts and "5" in texts  # similarity groups shown

    def test_info_tab_minimal_video_uses_fallbacks(self):
        # duration None, no codecs, no frame rate den, no audio bit rate,
        # no similarity ids -> every N/A branch.
        info = VideoPropertiesDialog(_video(unreadable=True), [])._build_info()
        texts = _texts(info)
        assert texts.count("N/A") >= 5
        assert "Similarity Group:" not in texts
        readable_row = texts[texts.index("Readable:") + 1]
        assert readable_row == "No"  # unreadable -> Readable: No
