"""
Tests for RedundantValuesDialog.

The dialog previews which property values of a single video would be removed
because its own file path (or mere file title) and meta title already carry
them.
"""

import pytest
from PySide6.QtWidgets import QWidget

from pysaurus.interface.kyuti.dialogs.redundant_values_dialog import (
    RedundantValuesDialog,
)
from pysaurus.properties.properties import PropType

FILE_PATH = r"C:\films\bluray\titanic, avec Leonardo DiCaprio.mkv"
FILE_TITLE = "titanic, avec Leonardo DiCaprio"


class FakeVideo:
    """Minimal stand-in for the video fields the dialog reads."""

    def __init__(self, filename, file_title, meta_title, properties):
        self.filename = filename
        self.file_title = file_title
        self.meta_title = meta_title
        self.properties = properties


@pytest.fixture
def prop_types():
    return [
        PropType(name="actor", type="str", multiple=True, default=[], enumeration=None),
        PropType(
            name="source", type="str", multiple=False, default=[""], enumeration=None
        ),
        PropType(name="genre", type="str", multiple=True, default=[], enumeration=None),
        PropType(
            name="rating", type="int", multiple=False, default=[0], enumeration=None
        ),
    ]


@pytest.fixture
def video():
    return FakeVideo(
        filename=FILE_PATH,
        file_title=FILE_TITLE,
        meta_title="Titanic",
        properties={
            "actor": ["Leonardo DiCaprio", "Kate Winslet"],
            "source": ["BluRay"],
            "rating": [5],
        },
    )


@pytest.fixture
def dialog(qtbot, video, prop_types):
    # "BluRay" is a parent folder, so it is redundant with the path only.
    dlg = RedundantValuesDialog(
        video,
        prop_types,
        {"actor": ["Leonardo DiCaprio"], "source": ["BluRay"]},
        {"actor": ["Leonardo DiCaprio"]},
    )
    qtbot.addWidget(dlg)
    return dlg


def _checked(dialog):
    """Return {property: [values still marked for removal]}."""
    return {
        name: [value for value, check in boxes if check.isChecked()]
        for name, boxes in dialog._value_boxes.items()
    }


class TestDisplay:
    def test_creation(self, dialog):
        assert dialog.windowTitle() == "Remove redundant values"

    def test_lists_only_text_properties_holding_values(self, dialog):
        # "rating" is an int, "genre" has no value on this video.
        assert [pt.name for pt in dialog._props] == ["actor", "source"]

    def test_full_path_is_the_default_mode(self, dialog):
        assert dialog.path_check.isChecked()
        assert dialog._file_caption.text() == "File path:"
        assert dialog._file_text.text() == FILE_PATH

    def test_redundant_values_are_checked_and_struck_through(self, dialog):
        for boxes in dialog._value_boxes.values():
            for _, check in boxes:
                assert check.isChecked()
                assert check.font().strikeOut()

    def test_only_redundant_values_get_a_check_box(self, dialog):
        assert _checked(dialog) == {
            "actor": ["Leonardo DiCaprio"],
            "source": ["BluRay"],
        }

    def test_count_label_and_clean_button(self, dialog):
        assert dialog.count_label.text() == "2 value(s) will be removed."
        assert dialog.clean_button.isEnabled()


class TestPathMode:
    def test_dropping_the_path_narrows_the_preview(self, dialog):
        dialog.path_check.setChecked(False)

        assert _checked(dialog) == {"actor": ["Leonardo DiCaprio"]}
        assert dialog.count_label.text() == "1 value(s) will be removed."

    def test_dropping_the_path_switches_the_matched_text(self, dialog):
        dialog.path_check.setChecked(False)

        assert dialog._file_caption.text() == "File title:"
        assert dialog._file_text.text() == FILE_TITLE

    def test_going_back_to_the_path_widens_the_preview_again(self, dialog):
        dialog.path_check.setChecked(False)
        dialog.path_check.setChecked(True)

        assert _checked(dialog) == {
            "actor": ["Leonardo DiCaprio"],
            "source": ["BluRay"],
        }
        assert dialog._file_text.text() == FILE_PATH

    def test_switching_leaves_no_stale_block_behind(self, dialog):
        dialog.path_check.setChecked(False)
        dialog.path_check.setChecked(True)

        content = dialog._content_layout.parentWidget()
        blocks = [child for child in content.children() if isinstance(child, QWidget)]
        assert len(blocks) == len(dialog._props)

    def test_spared_values_survive_a_mode_switch(self, dialog):
        _, check = dialog._value_boxes["actor"][0]
        check.setChecked(False)

        dialog.path_check.setChecked(False)
        assert _checked(dialog) == {"actor": []}

        dialog.path_check.setChecked(True)
        assert _checked(dialog) == {"actor": [], "source": ["BluRay"]}
        assert dialog.count_label.text() == "1 value(s) will be removed."


class TestInteraction:
    def test_unchecking_a_value_spares_it(self, dialog):
        _, check = dialog._value_boxes["actor"][0]
        check.setChecked(False)

        assert not check.font().strikeOut()
        assert dialog.count_label.text() == "1 value(s) will be removed."
        assert dialog.clean_button.isEnabled()

    def test_unchecking_a_property_spares_all_its_values(self, dialog):
        dialog._prop_boxes["actor"].setChecked(False)

        assert not any(check.isChecked() for _, check in dialog._value_boxes["actor"])
        assert dialog.count_label.text() == "1 value(s) will be removed."

    def test_header_follows_its_values(self, dialog):
        _, check = dialog._value_boxes["actor"][0]
        check.setChecked(False)
        assert not dialog._prop_boxes["actor"].isChecked()

        check.setChecked(True)
        assert dialog._prop_boxes["actor"].isChecked()

    def test_sparing_everything_disables_the_clean_button(self, dialog):
        for name in list(dialog._prop_boxes):
            dialog._prop_boxes[name].setChecked(False)

        assert dialog.count_label.text() == "0 value(s) will be removed."
        assert not dialog.clean_button.isEnabled()


class TestResult:
    def test_result_before_accepting_is_empty(self, dialog):
        assert dialog.get_result() == {}

    def test_accept_reports_every_checked_value(self, dialog):
        dialog._on_accept()

        assert dialog.get_result() == {
            "actor": ["Leonardo DiCaprio"],
            "source": ["BluRay"],
        }

    def test_accept_skips_spared_values_and_empty_properties(self, dialog):
        dialog._prop_boxes["actor"].setChecked(False)
        dialog._on_accept()

        assert dialog.get_result() == {"source": ["BluRay"]}

    def test_accept_reports_the_current_mode_only(self, dialog):
        dialog.path_check.setChecked(False)
        dialog._on_accept()

        assert dialog.get_result() == {"actor": ["Leonardo DiCaprio"]}


class TestNothingToClean:
    @pytest.fixture
    def empty_dialog(self, qtbot, video, prop_types):
        dlg = RedundantValuesDialog(video, prop_types, {}, {})
        qtbot.addWidget(dlg)
        return dlg

    def test_reports_no_redundant_value(self, empty_dialog):
        assert empty_dialog.count_label.text() == "No redundant value found."
        assert not empty_dialog.clean_button.isEnabled()

    def test_properties_are_still_listed(self, empty_dialog):
        assert [pt.name for pt in empty_dialog._props] == ["actor", "source"]
        assert empty_dialog._value_boxes == {}

    def test_result_is_empty(self, empty_dialog):
        empty_dialog._on_accept()

        assert empty_dialog.get_result() == {}
