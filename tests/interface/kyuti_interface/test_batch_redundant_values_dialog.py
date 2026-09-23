"""BatchRedundantValuesDialog: sum up what the cleanup would remove across a
selection, follow the path switch and the property choice, and hand back the
matching removals."""

from PySide6.QtWidgets import QDialog

from pysaurus.interface.kyuti.dialogs.batch_redundant_values_dialog import (
    BatchRedundantValuesDialog,
)

IN_PATH = {1: {"actor": ["a", "b"], "genre": ["x"]}, 2: {"actor": ["c"]}}
IN_TITLE = {1: {"actor": ["a"]}}


def _dialog(qtbot, in_path=IN_PATH, in_title=IN_TITLE):
    dialog = BatchRedundantValuesDialog(5, in_path, in_title)
    qtbot.addWidget(dialog)
    return dialog


def _labels(dialog):
    return {name: check.text() for name, check in dialog._prop_boxes.items()}


def test_path_mode_is_the_default_with_every_property_ticked(qtbot):
    dialog = _dialog(qtbot)
    assert "5 selected video(s)" in dialog._description.text()
    assert dialog.path_check.isChecked()
    assert _labels(dialog) == {
        "actor": "actor: 3 value(s)",
        "genre": "genre: 1 value(s)",
    }
    assert all(c.isChecked() and c.isEnabled() for c in dialog._prop_boxes.values())
    assert dialog.summary_label.text() == "4 value(s) will be removed from 2 video(s)."
    assert dialog.clean_button.isEnabled()
    assert dialog.get_result() == IN_PATH


def test_title_mode_relabels_and_disables_absent_properties(qtbot):
    dialog = _dialog(qtbot)
    dialog.path_check.setChecked(False)
    assert _labels(dialog) == {
        "actor": "actor: 1 value(s)",
        "genre": "genre: 0 value(s)",
    }
    assert not dialog._prop_boxes["genre"].isEnabled()
    assert dialog.summary_label.text() == "1 value(s) will be removed from 1 video(s)."
    assert dialog.get_result() == IN_TITLE


def test_unticked_properties_are_left_alone(qtbot):
    dialog = _dialog(qtbot)
    dialog._prop_boxes["actor"].setChecked(False)
    assert dialog.get_result() == {1: {"genre": ["x"]}}
    assert dialog.summary_label.text() == "1 value(s) will be removed from 1 video(s)."

    dialog._prop_boxes["genre"].setChecked(False)
    assert dialog.get_result() == {}
    assert dialog.summary_label.text() == "No property selected."
    assert not dialog.clean_button.isEnabled()


def test_property_choice_survives_a_mode_switch(qtbot):
    dialog = _dialog(qtbot)
    dialog._prop_boxes["actor"].setChecked(False)
    dialog.path_check.setChecked(False)
    assert dialog.get_result() == {}
    dialog.path_check.setChecked(True)
    assert not dialog._prop_boxes["actor"].isChecked()
    assert dialog.get_result() == {1: {"genre": ["x"]}}


def test_nothing_found_disables_clean(qtbot):
    dialog = _dialog(qtbot, in_path={}, in_title={})
    assert dialog._prop_boxes == {}
    assert dialog.summary_label.text() == "No redundant value found."
    assert not dialog.clean_button.isEnabled()


def test_clean_accepts_with_the_current_choice(qtbot):
    dialog = _dialog(qtbot)
    dialog.path_check.setChecked(False)
    dialog.clean_button.click()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.get_result() == IN_TITLE
