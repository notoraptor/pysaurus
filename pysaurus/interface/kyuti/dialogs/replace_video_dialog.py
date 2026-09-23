"""Confirmation for "Replace with": copy a video's infos, then remove it."""

from typing import Literal

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from pysaurus.core.language import say
from pysaurus.interface.kyuti.dialogs.video_confirm_dialog import video_header
from pysaurus.video.video_pattern import VideoPattern

RemovalMode = Literal["trash", "delete", "entry"]


class ReplaceVideoDialog(QDialog):
    """Show the video to remove and let the user pick how it goes.

    A found video can go to the trash or be deleted; a missing one only loses
    its entry. `note` is appended to the message (e.g. why titles won't be
    copied).
    """

    def __init__(
        self, video: VideoPattern, dst_title: str, note: str | None = None, parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(say("Replace Video"))
        self.setMinimumWidth(450)
        self._mode: RemovalMode | None = None

        layout = QVBoxLayout(self)
        layout.addLayout(video_header(video))

        message = say(
            "Copy this video's properties, titles, watched status and date added "
            "to '{target}', then remove it.",
            target=dst_title,
        )
        if video.not_found:
            message += "\n\n" + say(
                "The file is already missing: only the database entry goes."
            )
        if note:
            message += "\n\n" + note
        self._message = QLabel(message)
        self._message.setWordWrap(True)
        self._message.setStyleSheet("padding: 8px 0;")
        layout.addWidget(self._message)

        buttons = QDialogButtonBox()
        self._buttons: dict[RemovalMode, object] = {}
        if video.not_found:
            choices = [
                ("entry", say("Remove entry"), QDialogButtonBox.ButtonRole.AcceptRole)
            ]
        else:
            choices = [
                ("trash", say("Move to Trash"), QDialogButtonBox.ButtonRole.AcceptRole),
                (
                    "delete",
                    say("Delete permanently"),
                    QDialogButtonBox.ButtonRole.DestructiveRole,
                ),
            ]
        for mode, label, role in choices:
            button = buttons.addButton(label, role)
            button.clicked.connect(lambda _=False, m=mode: self._choose(m))
            self._buttons[mode] = button
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        buttons.rejected.connect(self.reject)
        self._buttons[choices[0][0]].setDefault(True)
        layout.addWidget(buttons)

    def _choose(self, mode: RemovalMode) -> None:
        self._mode = mode
        self.accept()

    @classmethod
    def ask(
        cls, video: VideoPattern, dst_title: str, note: str | None = None, parent=None
    ) -> RemovalMode | None:
        """Show the dialog; return the chosen removal mode, or None if cancelled."""
        dialog = cls(video, dst_title, note, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog._mode
        return None
