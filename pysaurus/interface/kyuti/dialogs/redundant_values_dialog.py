"""
Dialog for removing property values already carried by a video's own titles.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QLabel,
    QScrollArea,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.language import say
from pysaurus.properties.properties import PropType, PropUnitType
from pysaurus.video.video_pattern import VideoPattern

# Left margin aligning a plain value label with the text of a value check box.
_VALUE_INDENT = 24


class RedundantValuesDialog(QDialog):
    """
    Preview and confirm the removal of a video's redundant property values.

    Every text property holding a value on the video is listed with all its
    values. Values found in the matched-against texts are shown struck through
    and checked: those are the ones the dialog reports for removal. Any of them
    can be spared by unchecking it, and a whole property can be left alone by
    unchecking its header.

    The file path can be matched instead of the mere file title, which also
    brings in parent folders and the extension. Switching rebuilds the preview,
    but values spared by hand stay spared.
    """

    def __init__(
        self,
        video: VideoPattern,
        prop_types: list[PropType],
        redundant_in_path: dict[str, list[PropUnitType]],
        redundant_in_title: dict[str, list[PropUnitType]],
        parent=None,
    ):
        super().__init__(parent)
        self.video = video
        self._redundant = {True: redundant_in_path, False: redundant_in_title}
        # (property name, value) pairs the user asked to keep.
        self._spared: set[tuple[str, PropUnitType]] = set()
        # {property name: [(value, check box)]}, rebuilt on every mode switch.
        self._value_boxes: dict[str, list[tuple[PropUnitType, QCheckBox]]] = {}
        self._prop_boxes: dict[str, QCheckBox] = {}
        self._result: dict[str, list[PropUnitType]] = {}

        self._props = [
            pt
            for pt in prop_types
            if pt.type == "str" and video.properties.get(pt.name)
        ]
        # Left margin lining a plain value up with the text of a value check box.
        self._label_offset = self.style().pixelMetric(
            QStyle.PixelMetric.PM_IndicatorWidth
        ) + self.style().pixelMetric(QStyle.PixelMetric.PM_CheckBoxLabelSpacing)

        self.setWindowTitle(say("Remove redundant values"))
        self.setMinimumSize(520, 460)
        self._setup_ui()
        self._rebuild_blocks()

    # =========================================================================
    # Construction
    # =========================================================================

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        desc = QLabel(
            say(
                "Struck-through values already appear in the texts below, so "
                "removing them loses no information. "
                "Click a value to keep it anyway."
            )
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(desc)

        layout.addWidget(self._build_matched_box())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.StyledPanel)
        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(8, 8, 8, 8)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        self.count_label = QLabel()
        self.count_label.setWordWrap(True)
        layout.addWidget(self.count_label)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.clean_button = self.button_box.addButton(
            say("Clean"), QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _build_matched_box(self) -> QGroupBox:
        """Show the texts the values are matched against, and the path switch."""
        box = QGroupBox(say("Matched against"))
        box_layout = QVBoxLayout(box)

        form = QFormLayout()
        self._file_caption = QLabel()
        self._file_text = QLabel()
        self._file_text.setWordWrap(True)
        self._file_text.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        form.addRow(self._file_caption, self._file_text)
        if self.video.meta_title:
            meta_text = QLabel(self.video.meta_title)
            meta_text.setWordWrap(True)
            meta_text.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            form.addRow(say("Meta title:"), meta_text)
        box_layout.addLayout(form)

        self.path_check = QCheckBox(say("Include the full file path"))
        self.path_check.setChecked(True)
        self.path_check.setToolTip(
            say("Parent folder names and the file extension then count as well.")
        )
        self.path_check.toggled.connect(self._on_mode_toggled)
        box_layout.addWidget(self.path_check)

        self._update_matched_text()
        return box

    def _update_matched_text(self):
        """Show the very text the current mode matches against."""
        if self.path_check.isChecked():
            self._file_caption.setText(say("File path:"))
            self._file_text.setText(str(self.video.filename))
        else:
            self._file_caption.setText(say("File title:"))
            self._file_text.setText(self.video.file_title)

    def _rebuild_blocks(self):
        """Rebuild every property block for the current mode."""
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                # Unparent right away: deleteLater() alone leaves the old block
                # painted over the new one until the event loop catches up.
                widget.setParent(None)
                widget.deleteLater()
        self._value_boxes = {}
        self._prop_boxes = {}
        for prop_type in self._props:
            self._content_layout.addWidget(self._build_property_block(prop_type))
        self._content_layout.addStretch()
        self._update_state()

    def _build_property_block(self, prop_type: PropType) -> QWidget:
        """Build the header and the value rows of one property."""
        block = QWidget()
        block_layout = QVBoxLayout(block)
        block_layout.setContentsMargins(0, 0, 0, 8)
        block_layout.setSpacing(2)

        name = prop_type.name
        redundant = set(self._redundant[self.path_check.isChecked()].get(name, ()))
        if redundant:
            header = QCheckBox(name)
            header.setStyleSheet("font-weight: bold;")
            header.toggled.connect(
                lambda checked, n=name: self._on_prop_toggled(n, checked)
            )
            self._prop_boxes[name] = header
            block_layout.addWidget(header)
        else:
            label_header = QLabel(name)
            label_header.setStyleSheet("font-weight: bold;")
            block_layout.addWidget(label_header)

        # Indent from the layout: a check box ignores its own contents margins.
        values_layout = QVBoxLayout()
        values_layout.setContentsMargins(_VALUE_INDENT, 0, 0, 0)
        values_layout.setSpacing(2)
        block_layout.addLayout(values_layout)

        boxes: list[tuple[PropUnitType, QCheckBox]] = []
        for value in sorted(self.video.properties[name], key=str):
            if value in redundant:
                check = QCheckBox(str(value))
                check.setChecked((name, value) not in self._spared)
                check.toggled.connect(
                    lambda checked, n=name, v=value: self._on_value_toggled(
                        n, v, checked
                    )
                )
                boxes.append((value, check))
                values_layout.addWidget(check)
            else:
                label = QLabel(str(value))
                label.setWordWrap(True)
                label.setContentsMargins(self._label_offset, 0, 0, 0)
                values_layout.addWidget(label)
        if boxes:
            self._value_boxes[name] = boxes
            header = self._prop_boxes[name]
            header.blockSignals(True)
            header.setChecked(any(check.isChecked() for _, check in boxes))
            header.blockSignals(False)
        return block

    # =========================================================================
    # Interaction
    # =========================================================================

    def _on_mode_toggled(self):
        """Switch between matching the whole path and the file title only."""
        self._update_matched_text()
        self._rebuild_blocks()

    def _on_value_toggled(self, name: str, value: PropUnitType, checked: bool):
        """Remember a value the user chose to keep, or gave back."""
        if checked:
            self._spared.discard((name, value))
        else:
            self._spared.add((name, value))
        self._update_state()

    def _on_prop_toggled(self, name: str, checked: bool):
        """Toggle every value of a property along with its header."""
        for value, check in self._value_boxes.get(name, ()):
            if checked:
                self._spared.discard((name, value))
            else:
                self._spared.add((name, value))
            check.blockSignals(True)
            check.setChecked(checked)
            check.blockSignals(False)
        self._update_state()

    def _update_state(self):
        """Refresh strike-through, the removal count and the Clean button."""
        count = 0
        for name, boxes in self._value_boxes.items():
            checked_here = sum(check.isChecked() for _, check in boxes)
            for _, check in boxes:
                font = check.font()
                font.setStrikeOut(check.isChecked())
                check.setFont(font)
            count += checked_here
            header = self._prop_boxes.get(name)
            if header is not None and header.isChecked() != bool(checked_here):
                # The header follows its values: all spared means property spared.
                header.blockSignals(True)
                header.setChecked(bool(checked_here))
                header.blockSignals(False)
        if self._value_boxes:
            self.count_label.setText(
                say("{count} value(s) will be removed.", count=count)
            )
        else:
            self.count_label.setText(say("No redundant value found."))
        self.clean_button.setEnabled(bool(count))

    def _on_accept(self):
        self._result = {
            name: values
            for name, values in (
                (name, [value for value, check in boxes if check.isChecked()])
                for name, boxes in self._value_boxes.items()
            )
            if values
        }
        self.accept()

    def get_result(self) -> dict[str, list[PropUnitType]]:
        """Return {property name: [values to remove]}."""
        return self._result
