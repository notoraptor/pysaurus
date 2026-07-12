"""
Dialog for editing database sources (folders and files).
"""

import os

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from pysaurus.core.constants import VIDEO_SUPPORTED_EXTENSIONS
from pysaurus.core.language import say


def _normalize_path(path: str) -> str:
    """Normalize a path to absolute with system separators."""
    return os.path.normpath(os.path.abspath(path))


class EditFoldersDialog(QDialog):
    """
    Dialog for editing database sources.

    Allows adding, removing, and viewing folder and file paths.
    """

    def __init__(self, folders: list[str], database_name: str = "", parent=None):
        super().__init__(parent)
        self._database_name = database_name
        # Normalize paths and use a set to avoid duplicates
        self._folders: set[str] = {_normalize_path(f) for f in folders}
        self._result_folders: list[str] | None = None

        self._setup_ui()
        self._load_folders()

    def _setup_ui(self):
        """Set up the UI."""
        title = say("Edit Database Folders")
        if self._database_name:
            title = say(
                "Edit Folders - {database_name}", database_name=self._database_name
            )
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)

        # Instructions
        layout.addWidget(
            QLabel(say("Manage the sources (folders and files) for this database:"))
        )

        # Folder list
        self._list_widget = QListWidget()
        self._list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list_widget)

        # Buttons for source management
        btn_layout = QHBoxLayout()

        self._btn_add_folder = QPushButton(say("Add Folder..."))
        self._btn_add_folder.clicked.connect(self._on_add_folder)
        btn_layout.addWidget(self._btn_add_folder)

        self._btn_add_file = QPushButton(say("Add File..."))
        self._btn_add_file.clicked.connect(self._on_add_file)
        btn_layout.addWidget(self._btn_add_file)

        self._btn_remove = QPushButton(say("Remove Selected"))
        self._btn_remove.clicked.connect(self._on_remove_selected)
        self._btn_remove.setEnabled(False)
        btn_layout.addWidget(self._btn_remove)

        btn_layout.addStretch()

        self._count_label = QLabel()
        btn_layout.addWidget(self._count_label)

        layout.addLayout(btn_layout)

        # Dialog buttons
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self._on_accept)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

    def _load_folders(self):
        """Load folders into the list widget."""
        self._list_widget.clear()
        for folder in sorted(self._folders):
            self._list_widget.addItem(QListWidgetItem(folder))
        self._update_count()

    def _update_count(self):
        """Update the source count label."""
        count = len(self._folders)
        if count == 1:
            self._count_label.setText(say("1 source"))
        else:
            self._count_label.setText(say("{count} sources", count=count))

    def _on_selection_changed(self):
        """Handle selection changes."""
        has_selection = bool(self._list_widget.selectedItems())
        self._btn_remove.setEnabled(has_selection)

    def _on_add_folder(self):
        """Add a new folder."""
        folder = QFileDialog.getExistingDirectory(
            self, say("Select Folder"), "", QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            folder = _normalize_path(folder)
            if folder in self._folders:
                QMessageBox.information(
                    self,
                    say("Already in List"),
                    say("This folder is already in the list:\n{folder}", folder=folder),
                )
            else:
                self._folders.add(folder)
                self._load_folders()

    def _on_add_file(self):
        """Add video files."""
        ext_filter = " ".join(f"*.{ext}" for ext in sorted(VIDEO_SUPPORTED_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self,
            say("Select Video Files"),
            "",
            say("Video files ({ext_filter});;All files (*)", ext_filter=ext_filter),
        )
        added = 0
        for file in files:
            file = _normalize_path(file)
            if file not in self._folders:
                self._folders.add(file)
                added += 1
        if added > 0:
            self._load_folders()
        if files and added < len(files):
            skipped = len(files) - added
            QMessageBox.information(
                self,
                say("Some Files Already in List"),
                say("{skipped} file(s) were already in the list.", skipped=skipped),
            )

    def _on_remove_selected(self):
        """Remove selected sources."""
        selected_items = self._list_widget.selectedItems()
        if not selected_items:
            return

        # Confirm removal
        count = len(selected_items)
        if count == 1:
            msg = say(
                "Remove this source?\n\n{source}", source=selected_items[0].text()
            )
        else:
            msg = say("Remove {count} sources?", count=count)

        reply = QMessageBox.question(
            self,
            say("Confirm Removal"),
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                self._folders.discard(item.text())
            self._load_folders()

    def _on_accept(self):
        """Handle accept."""
        if not self._folders:
            reply = QMessageBox.warning(
                self,
                say("No Sources"),
                say(
                    "The database has no sources.\n\nAre you sure you want to continue?"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._result_folders = list(self._folders)
        self.accept()

    def get_folders(self) -> list[str] | None:
        """Return the folder list, or None if cancelled."""
        return self._result_folders

    @classmethod
    def edit_folders(
        cls, folders: list[str], database_name: str = "", parent=None
    ) -> list[str] | None:
        """
        Static method to show the dialog and return the edited folders.

        Returns the folder list if OK was clicked, None if cancelled.
        """
        dialog = cls(folders, database_name, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_folders()
        return None
