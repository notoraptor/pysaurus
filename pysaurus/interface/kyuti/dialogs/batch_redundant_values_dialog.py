"""Confirmation for cleaning redundant property values across a selection."""

from collections import Counter

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QVBoxLayout,
)

from pysaurus.core.language import say
from pysaurus.properties.properties import PropUnitType

Removals = dict[int, dict[str, list[PropUnitType]]]


class BatchRedundantValuesDialog(QDialog):
    """Sum up the values the cleanup would remove and let the user confirm.

    Unlike RedundantValuesDialog, values cannot be spared one by one: the user
    picks the properties to clean, and whether the full file path counts. The
    property boxes and the summary follow the mode; unticked boxes stay so.
    """

    def __init__(
        self,
        nb_videos: int,
        redundant_in_path: Removals,
        redundant_in_title: Removals,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(say("Remove redundant values"))
        self.setMinimumWidth(420)
        self._redundant = {True: redundant_in_path, False: redundant_in_title}

        layout = QVBoxLayout(self)
        self._description = QLabel(
            say(
                "Values already carried by a video's own titles will be removed "
                "from the {count} selected video(s). Untick a property to leave "
                "it alone; to spare single values, use the action of each video "
                "instead.",
                count=nb_videos,
            )
        )
        self._description.setWordWrap(True)
        layout.addWidget(self._description)

        self.path_check = QCheckBox(say("Include the full file path"))
        self.path_check.setChecked(True)
        self.path_check.setToolTip(
            say("Parent folder names and the file extension then count as well.")
        )
        self.path_check.toggled.connect(self._update_summary)
        layout.addWidget(self.path_check)

        props_box = QGroupBox(say("Properties to clean"))
        props_layout = QVBoxLayout(props_box)
        self._prop_boxes: dict[str, QCheckBox] = {}
        names = {
            name
            for found in self._redundant.values()
            for by_prop in found.values()
            for name in by_prop
        }
        for name in sorted(names):
            check = QCheckBox()
            check.setChecked(True)
            check.toggled.connect(self._update_summary)
            self._prop_boxes[name] = check
            props_layout.addWidget(check)
        layout.addWidget(props_box)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("padding: 8px 0;")
        layout.addWidget(self.summary_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.clean_button = buttons.addButton(
            say("Clean"), QDialogButtonBox.ButtonRole.AcceptRole
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._update_summary()

    def _update_summary(self):
        """Relabel the property boxes for the current mode, then count what the
        ticked ones will remove."""
        counts: Counter[str] = Counter()
        for by_prop in self._redundant[self.path_check.isChecked()].values():
            for name, values in by_prop.items():
                counts[name] += len(values)
        for name, check in self._prop_boxes.items():
            count = counts.get(name, 0)
            check.setText(say("{name}: {count} value(s)", name=name, count=count))
            check.setEnabled(bool(count))
        result = self.get_result()
        total = sum(len(v) for by_prop in result.values() for v in by_prop.values())
        if total:
            text = say(
                "{count} value(s) will be removed from {videos} video(s).",
                count=total,
                videos=len(result),
            )
        elif counts:
            text = say("No property selected.")
        else:
            text = say("No redundant value found.")
        self.summary_label.setText(text)
        self.clean_button.setEnabled(bool(total))

    def get_result(self) -> Removals:
        """The removals of the current mode, restricted to the ticked
        properties: {video_id: {property: [values]}}, with no empty entry."""
        wanted = {name for name, check in self._prop_boxes.items() if check.isChecked()}
        result: Removals = {}
        for video_id, by_prop in self._redundant[self.path_check.isChecked()].items():
            kept = {name: values for name, values in by_prop.items() if name in wanted}
            if kept:
                result[video_id] = kept
        return result

    @classmethod
    def ask(
        cls,
        nb_videos: int,
        redundant_in_path: Removals,
        redundant_in_title: Removals,
        parent=None,
    ) -> Removals | None:
        """Show the dialog; return the removals to apply, or None if cancelled."""
        dialog = cls(nb_videos, redundant_in_path, redundant_in_title, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_result()
        return None
