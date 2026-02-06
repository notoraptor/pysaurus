"""
Dialog for renaming items (database, etc.).
"""

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout


class RenameDialog(QDialog):
    """
    Simple dialog for renaming an item.

    Shows a text field pre-filled with the current name.
    """

    def __init__(
        self, title: str, current_name: str, label: str = "New name:", parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)

        self._current_name = current_name
        self._new_name: str | None = None

        self._setup_ui(label)

    def _setup_ui(self, label: str):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        # Label
        layout.addWidget(QLabel(label))

        # Text input
        self._input = QLineEdit()
        self._input.setText(self._current_name)
        self._input.selectAll()
        self._input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._input)

        # Dialog buttons
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self._on_accept)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

        # Initial validation
        self._validate()

    def _on_text_changed(self, text: str):
        """Handle text changes."""
        self._validate()

    def _validate(self):
        """Validate input and enable/disable OK button."""
        text = self._input.text().strip()
        # Name must be non-empty and different from current
        is_valid = bool(text) and text != self._current_name
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(is_valid)

    def _on_accept(self):
        """Handle accept."""
        self._new_name = self._input.text().strip()
        self.accept()

    def get_new_name(self) -> str | None:
        """Return the new name, or None if cancelled."""
        return self._new_name

    @classmethod
    def get_name(
        cls, title: str, current_name: str, label: str = "New name:", parent=None
    ) -> str | None:
        """
        Static method to show the dialog and return the new name.

        Returns the new name if OK was clicked, None if cancelled.
        """
        dialog = cls(title, current_name, label, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_new_name()
        return None
