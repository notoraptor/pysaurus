"""Dialog for the settings stored in a database."""

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QVBoxLayout,
)

from pysaurus.core.language import say
from pysaurus.database.database_settings import DatabaseSettings


class DatabaseSettingsDialog(QDialog):
    """Edit a database's settings.

    `property_names` are the candidates for the generalize-title target; the
    caller filters them, the dialog only lists them after an "ask each time"
    entry that stands for no default.
    """

    def __init__(
        self,
        settings: DatabaseSettings,
        property_names: list[str],
        database_name: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(
            say("Database Settings - {database_name}", database_name=database_name)
            if database_name
            else say("Database Settings")
        )
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._generalize_combo = QComboBox()
        self._generalize_combo.addItem(say("(ask each time)"), None)
        for name in property_names:
            self._generalize_combo.addItem(name, name)
        current = settings.generalize_title_property
        index = self._generalize_combo.findData(current) if current else 0
        self._generalize_combo.setCurrentIndex(max(index, 0))
        form.addRow(
            say("Default property for generalized titles:"), self._generalize_combo
        )
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self) -> DatabaseSettings:
        return DatabaseSettings(
            generalize_title_property=self._generalize_combo.currentData()
        )

    @classmethod
    def edit_settings(
        cls,
        settings: DatabaseSettings,
        property_names: list[str],
        database_name: str = "",
        parent=None,
    ) -> DatabaseSettings | None:
        """Show the dialog; return the edited settings, or None if cancelled."""
        dialog = cls(settings, property_names, database_name, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_settings()
        return None
