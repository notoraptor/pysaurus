"""
Go to duration dialog: jump to the video whose length is nearest to a typed
duration.
"""

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from pysaurus.core.duration import Duration, parse_duration
from pysaurus.core.language import say


class GoToDurationDialog(QDialog):
    def __init__(self, force_sorting: bool, parent=None):
        """
        Args:
            force_sorting: True if the view is not sorted by length first, so
                accepting the dialog will replace the current sorting.
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(say("Go to Duration"))
        self.setModal(True)
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel(say("Go to nearest duration:")))
        self.duration_input = QLineEdit()
        self.duration_input.setPlaceholderText("1h30m15s / 1:30:15")
        self.duration_input.textChanged.connect(self._on_text_changed)
        input_layout.addWidget(self.duration_input)
        layout.addLayout(input_layout)

        hint = QLabel(say("Format: XhYmZs (each part optional), MM:SS or H:MM:SS."))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #555;")
        layout.addWidget(hint)

        self.warning_label = QLabel(
            say(
                "The view is not sorted by length: it will be sorted by length "
                "(ascending), replacing the current sorting."
            )
        )
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("color: #a05a00;")
        self.warning_label.setVisible(force_sorting)
        layout.addWidget(self.warning_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)

        self.duration_input.setFocus()

    def _on_text_changed(self, text: str):
        self.ok_button.setEnabled(parse_duration(text) is not None)

    def get_duration(self) -> Duration | None:
        return parse_duration(self.duration_input.text())

    @staticmethod
    def get_seconds(force_sorting: bool, parent=None) -> float | None:
        """Show the dialog; return the typed duration in seconds, or None if
        cancelled."""
        dialog = GoToDurationDialog(force_sorting, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            duration = dialog.get_duration()
            if duration is not None:
                return duration.t / Duration.S
        return None
