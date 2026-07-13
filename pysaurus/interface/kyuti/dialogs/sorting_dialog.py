"""
Dialog for setting video sorting.
"""

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.constants import VIDEO_DEFAULT_SORTING
from pysaurus.core.language import say
from pysaurus.interface.common.common import FIELD_MAP, Uniconst
from pysaurus.video.video_sorting import VideoSorting


class SortingDialog(QDialog):
    """
    Dialog for setting video sort order.

    Each criterion is a self-contained editable row: a dropdown to pick the
    field, a button to flip its direction, and buttons to move or remove it.
    ``self._entries`` (a list of ``[field, reverse]``) is the single source of
    truth; rows are rebuilt from it, so the field dropdowns never desync.
    """

    def __init__(
        self, current_sorting: list[tuple[str, bool]] | None = None, parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(say("Set Sorting"))
        self.setMinimumWidth(460)
        self.setMinimumHeight(350)

        self._entries: list[list] = [
            [field, reverse] for field, reverse in (current_sorting or [])
        ]

        self._setup_ui()
        self._render_rows()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(say("Sort by (first has highest priority):")))

        # One editable row per sort criterion.
        self.sort_list = QListWidget()
        layout.addWidget(self.sort_list)

        # Append a new criterion (first sortable field, ascending) to edit inline.
        self.btn_add = QPushButton(say("Add sort field"))
        self.btn_add.clicked.connect(self._on_add)
        layout.addWidget(self.btn_add)

        # Dialog buttons
        button_box = QDialogButtonBox()
        button_box.addButton(say("Apply"), QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(say("Reset"), QDialogButtonBox.ButtonRole.ResetRole)
        button_box.addButton(QDialogButtonBox.StandardButton.Cancel)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.clicked.connect(self._on_button_clicked)
        self._button_box = button_box

        layout.addWidget(button_box)

    # --- rendering -----------------------------------------------------------

    def _render_rows(self):
        """Rebuild the whole list from ``self._entries``."""
        self.sort_list.clear()
        for index in range(len(self._entries)):
            row = self._build_row(index)
            item = QListWidgetItem()
            item.setSizeHint(row.sizeHint())
            self.sort_list.addItem(item)
            self.sort_list.setItemWidget(item, row)

    def _build_row(self, index: int) -> QWidget:
        """Build the editable widget for the criterion at ``index``."""
        field, reverse = self._entries[index]

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(2, 2, 2, 2)

        field_combo = QComboBox()
        for field_info in FIELD_MAP.sortable:
            field_combo.addItem(field_info.title, field_info.name)
        combo_index = field_combo.findData(field)
        if combo_index < 0:
            # Unknown field (e.g. a saved sort on a field no longer sortable):
            # keep it selectable so the criterion is not silently dropped.
            field_combo.addItem(field, field)
            combo_index = field_combo.count() - 1
        field_combo.setCurrentIndex(combo_index)
        # Connect only after setting the index, so this initial set is silent.
        field_combo.currentIndexChanged.connect(
            lambda _=0, i=index, c=field_combo: self._on_field_changed(i, c)
        )
        row_layout.addWidget(field_combo, 1)

        btn_dir = QPushButton(self._direction_symbol(reverse))
        btn_dir.setFixedWidth(32)
        btn_dir.setToolTip(say("Toggle Direction"))
        btn_dir.clicked.connect(lambda _=False, i=index: self._toggle_direction(i))
        row_layout.addWidget(btn_dir)

        btn_up = QPushButton("↑")
        btn_up.setFixedWidth(32)
        btn_up.setToolTip(say("Move Up"))
        btn_up.setEnabled(index > 0)
        btn_up.clicked.connect(lambda _=False, i=index: self._move_up(i))
        row_layout.addWidget(btn_up)

        btn_down = QPushButton("↓")
        btn_down.setFixedWidth(32)
        btn_down.setToolTip(say("Move Down"))
        btn_down.setEnabled(index < len(self._entries) - 1)
        btn_down.clicked.connect(lambda _=False, i=index: self._move_down(i))
        row_layout.addWidget(btn_down)

        btn_remove = QPushButton(Uniconst.CROSS)
        btn_remove.setFixedWidth(32)
        btn_remove.setToolTip(say("Remove"))
        btn_remove.clicked.connect(lambda _=False, i=index: self._remove(i))
        row_layout.addWidget(btn_remove)

        return row

    @staticmethod
    def _direction_symbol(reverse: bool) -> str:
        return Uniconst.ARROW_DOWN if reverse else Uniconst.ARROW_UP

    @staticmethod
    def _default_entries() -> list[list]:
        """The default sort order (date modified, descending)."""
        return [
            [field, reverse] for field, reverse in VideoSorting(VIDEO_DEFAULT_SORTING)
        ]

    # --- mutations -----------------------------------------------------------

    def _on_add(self):
        """Append a new criterion (first sortable field, ascending)."""
        default_field = FIELD_MAP.sortable[0].name if FIELD_MAP.sortable else ""
        self._entries.append([default_field, False])
        self._render_rows()
        self.sort_list.setCurrentRow(len(self._entries) - 1)

    def _on_field_changed(self, index: int, combo: QComboBox):
        """Update the field of the criterion edited in-place (no rebuild)."""
        if 0 <= index < len(self._entries):
            self._entries[index][0] = combo.currentData()

    def _toggle_direction(self, index: int):
        """Toggle the direction of the criterion at ``index``."""
        if 0 <= index < len(self._entries):
            self._entries[index][1] = not self._entries[index][1]
            self._render_rows()
            self.sort_list.setCurrentRow(index)

    def _move_up(self, index: int):
        """Move the criterion at ``index`` up one position."""
        if 0 < index < len(self._entries):
            self._entries[index - 1], self._entries[index] = (
                self._entries[index],
                self._entries[index - 1],
            )
            self._render_rows()
            self.sort_list.setCurrentRow(index - 1)

    def _move_down(self, index: int):
        """Move the criterion at ``index`` down one position."""
        if 0 <= index < len(self._entries) - 1:
            self._entries[index + 1], self._entries[index] = (
                self._entries[index],
                self._entries[index + 1],
            )
            self._render_rows()
            self.sort_list.setCurrentRow(index + 1)

    def _remove(self, index: int):
        """Remove the criterion at ``index``."""
        if 0 <= index < len(self._entries):
            del self._entries[index]
            self._render_rows()

    def _on_button_clicked(self, button):
        """Handle button clicks."""
        role = self._button_box.buttonRole(button)
        if role == QDialogButtonBox.ButtonRole.ResetRole:
            self._entries = self._default_entries()
            self._render_rows()

    def get_sorting(self) -> list[tuple[str, bool]]:
        """Get the sorting settings as a list of (field, reverse) tuples."""
        return [(field, reverse) for field, reverse in self._entries]
