"""
Files page — inventory and cleanup of files in the database source folders.

Two tabs:
- "Others": manage non-video files (thumbnails, .nfo, .part, …). Left panel
  lists extensions (count + total size, "Trash all" button). Right panel shows
  the files for the currently selected extension, with a filter and actions
  to open the containing folder or send to trash.
- "Video stats": read-only per-extension stats with an "Indexed vs. Not indexed"
  breakdown. Indexed videos are managed from the regular Videos page.
"""

from __future__ import annotations

import os
import sys

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.file_size import FileSize
from pysaurus.database.algorithms.folder_scan import (
    EMPTY_FOLDER_EXT,
    FileInfo,
    FolderScanResult,
)
from pysaurus.interface.pyside6.app_context import AppContext


def _ext_display(ext: str) -> str:
    """Human-readable label for an extension key."""
    if ext == EMPTY_FOLDER_EXT:
        return "(empty folder)"
    return f".{ext}" if ext else "(no extension)"


def _ext_subject(ext: str, count: int) -> str:
    """Label for a trash-all confirmation message."""
    if ext == EMPTY_FOLDER_EXT:
        return f"all {count} empty folder(s)"
    if ext:
        return f"all {count} .{ext} file(s)"
    return f"all {count} file(s) with no extension"


# Ask for confirmation when a bulk trash operation exceeds this many files.
BULK_CONFIRM_THRESHOLD = 500


class _FileTableModel(QAbstractTableModel):
    """Virtualized model exposing a list of FileInfo filtered by substring."""

    HEADERS = ("Path", "Size")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all: list[FileInfo] = []
        self._visible: list[FileInfo] = []
        self._needle: str = ""

    def set_items(self, items: list[FileInfo]) -> None:
        self.beginResetModel()
        self._all = list(items)
        self._apply_filter()
        self.endResetModel()

    def set_filter(self, text: str) -> None:
        self.beginResetModel()
        self._needle = text.lower()
        self._apply_filter()
        self.endResetModel()

    def _apply_filter(self) -> None:
        if self._needle:
            self._visible = [
                info for info in self._all if self._needle in str(info.path).lower()
            ]
        else:
            self._visible = list(self._all)

    def file_at(self, row: int) -> FileInfo | None:
        return self._visible[row] if 0 <= row < len(self._visible) else None

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._visible)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return self.HEADERS[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        info = self._visible[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            col = index.column()
            if col == 0:
                return str(info.path)
            if col == 1:
                return str(FileSize(info.size))
        if role == Qt.ItemDataRole.TextAlignmentRole and index.column() == 1:
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None


class FilesPage(QWidget):
    """Scan DB folders and manage non-video files."""

    scan_requested = Signal()

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._result: FolderScanResult | None = None
        self._sorted_ext_keys: list[str] = []
        self._files_model = _FileTableModel(self)
        self._setup_ui()

    # =========================================================================
    # UI construction
    # =========================================================================

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        self._empty_widget = self._build_empty_widget()
        self._stack.addWidget(self._empty_widget)

        self._scanned_widget = self._build_scanned_widget()
        self._stack.addWidget(self._scanned_widget)

        self._stack.setCurrentWidget(self._empty_widget)

    def _build_empty_widget(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addStretch()

        title = QLabel("<b>Database file inventory</b>")
        title.setStyleSheet("font-size: 16px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(
            "Scan all files in the database source folders, then review and "
            "clean non-video files that have accumulated there "
            "(thumbnails, .nfo, .part, subtitles, …)."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #555; padding: 10px;")
        layout.addWidget(desc)

        btn = QPushButton("Scan folders")
        btn.setFixedWidth(200)
        btn.clicked.connect(self.scan_requested)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(btn)
        row.addStretch()
        layout.addLayout(row)

        layout.addStretch()
        return w

    def _build_scanned_widget(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)

        top = QHBoxLayout()
        self._rescan_btn = QPushButton("Rescan folders")
        self._rescan_btn.clicked.connect(self.scan_requested)
        top.addWidget(self._rescan_btn)
        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet("color: #555; padding-left: 10px;")
        top.addWidget(self._summary_label)
        top.addStretch()
        layout.addLayout(top)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_others_tab(), "Others")
        self._tabs.addTab(self._build_video_stats_tab(), "Video stats")
        layout.addWidget(self._tabs)

        return w

    def _build_others_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: extensions
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("<b>Extensions</b>"))

        self._ext_table = QTableWidget(0, 4)
        self._ext_table.setHorizontalHeaderLabels(
            ["Extension", "Count", "Total size", ""]
        )
        self._ext_table.verticalHeader().setVisible(False)
        self._ext_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._ext_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._ext_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        h = self._ext_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._ext_table.currentCellChanged.connect(
            lambda cur, _col, _p_cur, _p_col: self._on_ext_row_changed(cur)
        )
        left_layout.addWidget(self._ext_table)

        splitter.addWidget(left)

        # Right: files for selected extension
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_header = QHBoxLayout()
        self._files_title = QLabel("<b>Files</b>")
        right_header.addWidget(self._files_title)
        right_header.addStretch()
        right_layout.addLayout(right_header)

        actions = QHBoxLayout()
        self._btn_open_folder = QPushButton("Open folder")
        self._btn_open_folder.clicked.connect(self._on_open_selected_folder)
        self._btn_trash_selected = QPushButton("Send to trash")
        self._btn_trash_selected.clicked.connect(self._on_trash_selected)
        actions.addWidget(self._btn_open_folder)
        actions.addWidget(self._btn_trash_selected)
        actions.addStretch()
        actions.addWidget(QLabel("Filter:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Substring match on path")
        self._filter_edit.setClearButtonEnabled(True)
        self._filter_edit.textChanged.connect(self._files_model.set_filter)
        self._filter_edit.setFixedWidth(220)
        actions.addWidget(self._filter_edit)
        right_layout.addLayout(actions)

        self._files_view = QTableView()
        self._files_view.setModel(self._files_model)
        self._files_view.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._files_view.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self._files_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._files_view.verticalHeader().setVisible(False)
        self._files_view.setAlternatingRowColors(True)
        fh = self._files_view.horizontalHeader()
        fh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        fh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        right_layout.addWidget(self._files_view)

        splitter.addWidget(right)
        splitter.setSizes([320, 700])

        layout.addWidget(splitter)
        return w

    def _build_video_stats_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        hint = QLabel(
            "Read-only stats for video files. Use the <b>Videos</b> page to "
            "manage indexed videos. An <i>unknown</i> video is physically "
            "present on disk but not referenced by the database."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #555; padding: 4px 0;")
        layout.addWidget(hint)

        self._video_stats_table = QTableWidget(0, 5)
        self._video_stats_table.setHorizontalHeaderLabels(
            [
                "Extension",
                "Indexed (count)",
                "Indexed (size)",
                "Unknown (count)",
                "Unknown (size)",
            ]
        )
        self._video_stats_table.verticalHeader().setVisible(False)
        self._video_stats_table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self._video_stats_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        h = self._video_stats_table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._video_stats_table)

        return w

    # =========================================================================
    # Public API (called by main window)
    # =========================================================================

    def refresh(self) -> None:
        """Re-display state from the last known scan result."""
        result = self.ctx.get_last_scan_result()
        if result is None:
            self._result = None
            self._stack.setCurrentWidget(self._empty_widget)
        else:
            self._result = result
            self._populate_others_tab()
            self._populate_video_stats_tab()
            self._update_summary()
            self._stack.setCurrentWidget(self._scanned_widget)

    # =========================================================================
    # Others tab population and actions
    # =========================================================================

    def _populate_others_tab(self) -> None:
        assert self._result is not None
        others = self._result.others

        totals = [
            (ext, len(infos), sum(i.size for i in infos))
            for ext, infos in others.items()
        ]
        totals.sort(key=lambda row: (-row[2], row[0]))
        self._sorted_ext_keys = [row[0] for row in totals]

        self._ext_table.blockSignals(True)
        self._ext_table.setRowCount(len(totals))
        for row_index, (ext, count, size) in enumerate(totals):
            ext_item = QTableWidgetItem(_ext_display(ext))
            count_item = QTableWidgetItem(str(count))
            size_item = QTableWidgetItem(str(FileSize(size)))
            count_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            size_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self._ext_table.setItem(row_index, 0, ext_item)
            self._ext_table.setItem(row_index, 1, count_item)
            self._ext_table.setItem(row_index, 2, size_item)

            btn = QPushButton("Trash all")
            btn.setStyleSheet("color: #a40000;")
            btn.clicked.connect(
                lambda _checked=False, e=ext: self._on_trash_extension(e)
            )
            self._ext_table.setCellWidget(row_index, 3, btn)
        self._ext_table.blockSignals(False)

        if totals:
            self._ext_table.selectRow(0)
            self._on_ext_row_changed(0)
        else:
            self._files_title.setText("<b>Files</b>")
            self._files_model.set_items([])

    def _on_ext_row_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._sorted_ext_keys) or self._result is None:
            self._files_model.set_items([])
            self._files_title.setText("<b>Files</b>")
            return
        ext = self._sorted_ext_keys[row]
        items = self._result.others.get(ext, [])
        self._files_model.set_items(items)
        if ext == EMPTY_FOLDER_EXT:
            heading = "Empty folders"
        elif ext:
            heading = f"Files — .{ext}"
        else:
            heading = "Files — (no extension)"
        self._files_title.setText(f"<b>{heading}</b> ({len(items)})")

    def _selected_file_infos(self) -> list[FileInfo]:
        rows = {idx.row() for idx in self._files_view.selectionModel().selectedRows()}
        infos: list[FileInfo] = []
        for row in sorted(rows):
            info = self._files_model.file_at(row)
            if info is not None:
                infos.append(info)
        return infos

    def _on_open_selected_folder(self) -> None:
        infos = self._selected_file_infos()
        if not infos:
            QMessageBox.information(
                self, "No selection", "Select at least one file first."
            )
            return
        # Open the parent folder of the first selected file.
        parent = os.path.dirname(str(infos[0].path))
        _open_in_file_manager(parent)

    def _on_trash_selected(self) -> None:
        infos = self._selected_file_infos()
        if not infos:
            QMessageBox.information(
                self, "No selection", "Select at least one file first."
            )
            return
        if not self._confirm_trash(len(infos), preview_paths=infos):
            return
        self._execute_trash(infos)

    def _on_trash_extension(self, ext: str) -> None:
        if self._result is None:
            return
        infos = list(self._result.others.get(ext, []))
        if not infos:
            return
        if not self._confirm_trash(
            len(infos), what=_ext_subject(ext, len(infos)), preview_paths=infos
        ):
            return
        self._execute_trash(infos)

    def _confirm_trash(
        self,
        count: int,
        *,
        what: str | None = None,
        preview_paths: list[FileInfo] | None = None,
    ) -> bool:
        subject = what or f"{count} file(s)"
        detail = ""
        if preview_paths:
            head = [str(p.path) for p in preview_paths[:5]]
            detail = "\n".join(head)
            if len(preview_paths) > 5:
                detail += f"\n… (+{len(preview_paths) - 5} more)"
        warn_bulk = ""
        if count > BULK_CONFIRM_THRESHOLD:
            warn_bulk = (
                f"\n\nThis is a bulk operation ({count} files). "
                "It cannot be undone from Pysaurus; files will go to the "
                "system trash if available."
            )
        reply = QMessageBox.question(
            self,
            "Send to trash",
            f"Send {subject} to the system trash?{warn_bulk}\n\n{detail}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _execute_trash(self, infos: list[FileInfo]) -> None:
        ok, errors = self.ctx.trash_files([info.path for info in infos])
        failed_paths = {e[0] for e in errors}
        removed_paths = {str(info.path) for info in infos} - failed_paths
        self._drop_paths_from_others(removed_paths)
        self._populate_others_tab()
        self._populate_video_stats_tab()
        self._update_summary()

        if errors:
            detail = "\n".join(f"{p}: {msg}" for p, msg in errors[:10])
            if len(errors) > 10:
                detail += f"\n… (+{len(errors) - 10} more)"
            QMessageBox.warning(
                self,
                "Trash completed with errors",
                f"Sent {ok} file(s) to trash. {len(errors)} failed:\n\n{detail}",
            )

    def _drop_paths_from_others(self, removed_paths: set[str]) -> None:
        if self._result is None or not removed_paths:
            return
        new_others: dict[str, list[FileInfo]] = {}
        for ext, infos in self._result.others.items():
            kept = [i for i in infos if str(i.path) not in removed_paths]
            if kept:
                new_others[ext] = kept
        self._result.others = new_others

    # =========================================================================
    # Video stats tab population
    # =========================================================================

    def _populate_video_stats_tab(self) -> None:
        assert self._result is not None
        extensions = set(self._result.videos_indexed) | set(self._result.videos_unknown)

        rows: list[tuple[str, int, int, int, int]] = []
        for ext in extensions:
            idx = self._result.videos_indexed.get(ext, [])
            unk = self._result.videos_unknown.get(ext, [])
            rows.append(
                (
                    ext,
                    len(idx),
                    sum(i.size for i in idx),
                    len(unk),
                    sum(i.size for i in unk),
                )
            )
        rows.sort(key=lambda r: (-(r[2] + r[4]), r[0]))

        self._video_stats_table.setRowCount(len(rows))
        for i, (ext, ic, isz, uc, usz) in enumerate(rows):
            self._video_stats_table.setItem(i, 0, QTableWidgetItem(f".{ext}"))
            _set_numeric(self._video_stats_table, i, 1, str(ic))
            _set_numeric(self._video_stats_table, i, 2, str(FileSize(isz)))
            _set_numeric(self._video_stats_table, i, 3, str(uc))
            _set_numeric(self._video_stats_table, i, 4, str(FileSize(usz)))

    def _update_summary(self) -> None:
        if self._result is None:
            self._summary_label.setText("")
            return
        nb_others = sum(len(v) for v in self._result.others.values())
        size_others = sum(i.size for v in self._result.others.values() for i in v)
        nb_idx = sum(len(v) for v in self._result.videos_indexed.values())
        nb_unk = sum(len(v) for v in self._result.videos_unknown.values())
        self._summary_label.setText(
            f"{nb_others} other files ({FileSize(size_others)})  ·  "
            f"{nb_idx} indexed videos  ·  {nb_unk} unknown videos"
        )


def _set_numeric(table: QTableWidget, row: int, col: int, text: str) -> None:
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    table.setItem(row, col, item)


def _open_in_file_manager(path: str) -> None:
    if not path:
        return
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        import subprocess

        subprocess.Popen(["open", path])
    else:
        import subprocess

        subprocess.Popen(["xdg-open", path])
