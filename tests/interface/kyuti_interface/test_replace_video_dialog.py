"""ReplaceVideoDialog: trash or delete a found video, only drop the entry of a
missing one, and carry the note about titles."""

from PySide6.QtWidgets import QDialog

from pysaurus.interface.kyuti.dialogs.replace_video_dialog import ReplaceVideoDialog


def _dialog(qtbot, mock_context, video_id, note=None):
    dialog = ReplaceVideoDialog(mock_context.get_video_by_id(video_id), "target", note)
    qtbot.addWidget(dialog)
    return dialog


def test_found_video_offers_trash_by_default_and_delete(qtbot, mock_context):
    dialog = _dialog(qtbot, mock_context, 3)
    assert set(dialog._buttons) == {"trash", "delete"}
    assert dialog._buttons["trash"].isDefault()

    dialog._buttons["delete"].click()

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog._mode == "delete"


def test_trash_button_returns_trash(qtbot, mock_context):
    dialog = _dialog(qtbot, mock_context, 3)
    dialog._buttons["trash"].click()
    assert dialog._mode == "trash"


def test_missing_video_only_loses_its_entry(qtbot, mock_context, mock_database):
    next(v for v in mock_database._videos if v["video_id"] == 3)["found"] = False
    dialog = _dialog(qtbot, mock_context, 3)
    assert set(dialog._buttons) == {"entry"}
    assert dialog._buttons["entry"].isDefault()
    assert "already missing" in dialog._message.text()

    dialog._buttons["entry"].click()

    assert dialog._mode == "entry"


def test_note_is_appended_to_the_message(qtbot, mock_context):
    dialog = _dialog(qtbot, mock_context, 3, note="No titles today.")
    text = dialog._message.text()
    assert "'target'" in text
    assert text.endswith("No titles today.")
