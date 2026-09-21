"""DatabaseSettingsDialog: an "ask each time" entry, then the candidates."""

from pysaurus.database.database_settings import DatabaseSettings
from pysaurus.interface.kyuti.dialogs.database_settings_dialog import (
    DatabaseSettingsDialog,
)


def _items(dialog: DatabaseSettingsDialog) -> list[str]:
    combo = dialog._generalize_combo
    return [combo.itemText(i) for i in range(combo.count())]


def test_no_default_selects_ask_each_time(qtbot):
    dialog = DatabaseSettingsDialog(DatabaseSettings(), ["a", "b"], "db")
    qtbot.addWidget(dialog)
    assert _items(dialog)[1:] == ["a", "b"]
    assert dialog._generalize_combo.currentIndex() == 0
    assert dialog.get_settings() == DatabaseSettings()


def test_current_default_is_preselected_and_choice_is_returned(qtbot):
    dialog = DatabaseSettingsDialog(
        DatabaseSettings(generalize_title_property="b"), ["a", "b"]
    )
    qtbot.addWidget(dialog)
    assert dialog._generalize_combo.currentData() == "b"
    dialog._generalize_combo.setCurrentIndex(1)
    assert dialog.get_settings() == DatabaseSettings(generalize_title_property="a")


def test_unknown_default_falls_back_to_ask_each_time(qtbot):
    dialog = DatabaseSettingsDialog(
        DatabaseSettings(generalize_title_property="gone"), ["a"]
    )
    qtbot.addWidget(dialog)
    assert dialog.get_settings() == DatabaseSettings()
