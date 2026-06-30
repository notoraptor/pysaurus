"""Edit folders dialog — edit a database's source folders/files.

Passive: returns the folder list on OK. Reuses the databases-page pattern
(`videre.Dialog` native picker + add/dedup/remove). Reference:
kyuti/dialogs/edit_folders_dialog.py.
"""

from __future__ import annotations

import os

import videre
from videre.widgets.widget import Widget

_FOLDER = "\U0001f4c1"  # 📁
_FILE = "\U0001f4c4"  # 📄


class EditFoldersDialog(videre.Column):
    __wprops__ = {}
    __slots__ = ("_folders", "_list", "_message")

    def __init__(self, folders):
        self._folders: list[str] = list(folders)
        self._list = videre.Column([], space=2)
        self._message = videre.Text("", color=videre.Colors.red)
        super().__init__(
            [
                videre.Text("Source folders and files:"),
                videre.Container(
                    videre.ScrollView(self._list, wrap_horizontal=True),
                    height=240,
                    border=videre.Border.all(1, videre.Colors.lightgray),
                    padding=videre.Padding.all(4),
                ),
                videre.Row(
                    [
                        videre.Button("Add Folder", on_click=self._add_folder),
                        videre.Button("Add File", on_click=self._add_file),
                    ],
                    space=5,
                ),
                self._message,
            ],
            space=8,
            expand_horizontal=True,
        )
        self._populate()

    @staticmethod
    def _norm(path: str) -> str:
        return os.path.normpath(os.path.abspath(path))

    def _populate(self) -> None:
        rows = []
        for source in self._folders:
            emoji = _FOLDER if os.path.isdir(source) else _FILE
            rows.append(
                videre.Row(
                    [
                        videre.Button("✕", data=source, on_click=self._remove),
                        videre.Text(
                            f"{emoji} {source}", wrap=videre.TextWrap.CHAR, weight=1
                        ),
                    ],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                )
            )
        self._list.controls = rows or [videre.Text("(no source)", italic=True)]

    def _add(self, path: str) -> None:
        if not path:
            return
        norm = self._norm(path)
        if norm in {self._norm(s) for s in self._folders}:
            self._message.text = "This path is already in the list."
        else:
            self._folders.append(norm)
            self._message.text = ""
        self._populate()

    def _add_folder(self, widget) -> None:
        self._add(videre.Dialog.select_directory())

    def _add_file(self, widget) -> None:
        for path in videre.Dialog.select_many_files():
            self._add(path)

    def _remove(self, widget: Widget) -> None:
        self._folders = [s for s in self._folders if s != widget.data]
        self._populate()

    def get_folders(self) -> list[str]:
        return list(self._folders)
