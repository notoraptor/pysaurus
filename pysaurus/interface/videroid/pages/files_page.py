"""Files page — database file inventory (scan + Others / Video-stats tabs).

Reference: pyside6/pages/files_page.py. videre gaps worked around: no Tabs (G2)
→ a button toggle + content holder; no Table (G1) → a `Column` of weighted
`Row`s. Trash confirmation uses `window.confirm` (a page-level modal is fine —
unlike inside a dialog, cf. G-MODAL). The scan is a long op via `run_process`.
"""

from __future__ import annotations

import os
import subprocess
import sys

import videre
from videre.widgets.widget import Widget

from pysaurus.database.algorithms.folder_scan import EMPTY_FOLDER_EXT
from pysaurus.interface.videroid.pages.base_page import Page

_HEADER_BG = videre.parse_color((225, 225, 225))
_SELECTED_BG = videre.parse_color((227, 242, 253))
_BULK_THRESHOLD = 500


def _human_size(num: int) -> str:
    size = float(num)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _ext_label(ext) -> str:
    if ext == EMPTY_FOLDER_EXT:
        return "(empty folder)"
    return ext or "(no extension)"


class FilesPage(Page):
    title = "Files"

    def __init__(self, app):
        super().__init__(app)
        self._holder = videre.Container(weight=1)  # empty | scanned
        self._tab_holder = videre.Container(weight=1)  # Others | Video stats
        self._summary = videre.Text("")
        self._filter = videre.TextInput()
        self._result = None
        self._active_tab = "others"
        self._sel_ext = None
        self._selected_files: set = set()

    def build(self) -> Widget:
        self._reload()
        return self._holder

    def on_show(self) -> None:
        self._reload()

    def _reload(self) -> None:
        self._result = self.context.get_last_scan_result()
        self._sel_ext = None
        self._selected_files.clear()
        self._holder.control = (
            self._empty_state() if self._result is None else self._scanned_state()
        )

    # --- scan ---------------------------------------------------------------

    def _empty_state(self) -> Widget:
        return videre.Column(
            [
                videre.Text("Database file inventory", strong=True),
                videre.Text(
                    "Scan the database folders to inventory the non-video files "
                    "(thumbnails, .nfo, .part, subtitles…) accumulated next to "
                    "your videos."
                ),
                videre.Button("Scan folders", on_click=self._on_scan),
            ],
            space=10,
        )

    def _on_scan(self, widget) -> None:
        self.app.run_process(
            "Scanning files", self.context.scan_folders, self._after_scan
        )

    def _after_scan(self, end) -> None:
        self.app.show_page("files")

    # --- scanned state ------------------------------------------------------

    def _scanned_state(self) -> Widget:
        self._update_summary()
        column = videre.Column(
            [
                videre.Row(
                    [
                        videre.Button("Rescan folders", on_click=self._on_scan),
                        self._summary,
                    ],
                    space=10,
                    vertical_alignment=videre.Alignment.CENTER,
                ),
                videre.Row(
                    [
                        videre.Button("Others", data="others", on_click=self._on_tab),
                        videre.Button(
                            "Video stats", data="stats", on_click=self._on_tab
                        ),
                    ],
                    space=4,
                ),
                self._tab_holder,
            ],
            space=8,
            weight=1,
        )
        self._show_tab()
        return column

    def _update_summary(self) -> None:
        result = self._result
        n_others = sum(len(files) for files in result.others.values())
        size_others = sum(f.size for files in result.others.values() for f in files)
        n_indexed = sum(len(files) for files in result.videos_indexed.values())
        n_unknown = sum(len(files) for files in result.videos_unknown.values())
        self._summary.text = (
            f"{n_others} other files ({_human_size(size_others)}) · "
            f"{n_indexed} indexed videos · {n_unknown} unknown videos"
        )

    def _on_tab(self, widget) -> None:
        self._active_tab = widget.data
        self._show_tab()

    def _show_tab(self) -> None:
        self._tab_holder.control = (
            self._others_tab() if self._active_tab == "others" else self._stats_tab()
        )

    # --- "table" helpers ----------------------------------------------------

    def _cell(self, text, weight: int = 1, strong: bool = False) -> Widget:
        return videre.Container(
            videre.Text(str(text), strong=strong, wrap=videre.TextWrap.WORD),
            weight=weight,
            padding=videre.Padding.axis(vertical=3, horizontal=6),
        )

    def _header(self, columns) -> Widget:
        return videre.Container(
            videre.Row([self._cell(t, w, strong=True) for t, w in columns], space=0),
            background_color=_HEADER_BG,
        )

    # --- Others tab ---------------------------------------------------------

    def _others_tab(self) -> Widget:
        return videre.Row(
            [
                videre.Container(
                    self._ext_table(),
                    width=320,
                    border=videre.Border.all(1, videre.Colors.lightgray),
                ),
                videre.Container(
                    self._files_panel(),
                    weight=1,
                    border=videre.Border.all(1, videre.Colors.lightgray),
                ),
            ],
            space=6,
            weight=1,
        )

    def _ext_table(self) -> Widget:
        items = sorted(
            self._result.others.items(),
            key=lambda kv: (-sum(f.size for f in kv[1]), str(kv[0])),
        )
        if self._sel_ext is None and items:
            self._sel_ext = items[0][0]
        rows = [
            self._header([("Extension", 2), ("Count", 1), ("Total size", 2), ("", 1)])
        ]
        for ext, files in items:
            total = sum(f.size for f in files)
            rows.append(
                videre.Container(
                    videre.Row(
                        [
                            videre.Button(
                                _ext_label(ext),
                                data=ext,
                                on_click=self._select_ext,
                                weight=2,
                            ),
                            self._cell(len(files), 1),
                            self._cell(_human_size(total), 2),
                            videre.Container(
                                videre.Button(
                                    "Trash all", data=ext, on_click=self._trash_all
                                ),
                                weight=1,
                            ),
                        ],
                        space=0,
                        vertical_alignment=videre.Alignment.CENTER,
                    ),
                    background_color=_SELECTED_BG if ext == self._sel_ext else None,
                )
            )
        return videre.ScrollView(videre.Column(rows, space=0), wrap_horizontal=True)

    def _select_ext(self, widget) -> None:
        self._sel_ext = widget.data
        self._selected_files.clear()
        self._show_tab()

    def _files_panel(self) -> Widget:
        files = self._result.others.get(self._sel_ext, []) if self._sel_ext else []
        text = (self._filter.value or "").strip().lower()
        if text:
            files = [f for f in files if text in str(f.path).lower()]
        self._selected_files &= {str(f.path) for f in files}
        rows = [
            videre.Row(
                [
                    videre.Checkbox(
                        checked=str(f.path) in self._selected_files,
                        data=str(f.path),
                        on_change=self._on_file_check,
                    ),
                    videre.Text(str(f.path), weight=1, wrap=videre.TextWrap.CHAR),
                    videre.Text(_human_size(f.size)),
                ],
                space=5,
                vertical_alignment=videre.Alignment.CENTER,
            )
            for f in files
        ]
        return videre.Column(
            [
                videre.Row(
                    [
                        videre.Text(
                            f"Files — {_ext_label(self._sel_ext)} ({len(files)})",
                            strong=True,
                            weight=1,
                        ),
                        videre.Button("Open folder", on_click=self._open_folder),
                        videre.Button("Send to trash", on_click=self._trash_selected),
                    ],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                ),
                videre.Row(
                    [
                        videre.Text("Filter:"),
                        self._filter,
                        videre.Button("Apply", on_click=lambda w: self._show_tab()),
                    ],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                ),
                videre.Container(
                    videre.ScrollView(
                        videre.Column(
                            rows or [videre.Text("(no file)", italic=True)], space=2
                        ),
                        wrap_horizontal=True,
                    ),
                    weight=1,
                ),
            ],
            space=6,
            weight=1,
        )

    def _on_file_check(self, checkbox) -> None:
        if checkbox.checked:
            self._selected_files.add(checkbox.data)
        else:
            self._selected_files.discard(checkbox.data)

    # --- Video stats tab ----------------------------------------------------

    def _stats_tab(self) -> Widget:
        result = self._result
        exts = set(result.videos_indexed) | set(result.videos_unknown)

        def total(ext) -> int:
            indexed = sum(f.size for f in result.videos_indexed.get(ext, []))
            unknown = sum(f.size for f in result.videos_unknown.get(ext, []))
            return indexed + unknown

        rows = [
            self._header(
                [
                    ("Extension", 2),
                    ("Indexed", 1),
                    ("Indexed size", 2),
                    ("Unknown", 1),
                    ("Unknown size", 2),
                ]
            )
        ]
        for ext in sorted(exts, key=lambda e: (-total(e), str(e))):
            indexed = result.videos_indexed.get(ext, [])
            unknown = result.videos_unknown.get(ext, [])
            rows.append(
                videre.Row(
                    [
                        self._cell(_ext_label(ext), 2),
                        self._cell(len(indexed), 1),
                        self._cell(_human_size(sum(f.size for f in indexed)), 2),
                        self._cell(len(unknown), 1),
                        self._cell(_human_size(sum(f.size for f in unknown)), 2),
                    ],
                    space=0,
                )
            )
        return videre.ScrollView(videre.Column(rows, space=0), wrap_horizontal=True)

    # --- trash --------------------------------------------------------------

    def _trash_selected(self, widget) -> None:
        paths = sorted(self._selected_files)
        if paths:
            self._confirm_trash(paths, f"{len(paths)} file(s)")

    def _trash_all(self, widget) -> None:
        ext = widget.data
        paths = [str(f.path) for f in self._result.others.get(ext, [])]
        if paths:
            self._confirm_trash(paths, f"all {len(paths)} '{_ext_label(ext)}' file(s)")

    def _confirm_trash(self, paths, subject: str) -> None:
        lines = [videre.Text(f"Send {subject} to the system trash?")]
        for path in paths[:5]:
            lines.append(videre.Text(path, wrap=videre.TextWrap.CHAR))
        if len(paths) > 5:
            lines.append(videre.Text(f"… (+{len(paths) - 5} more)", italic=True))
        if len(paths) > _BULK_THRESHOLD:
            lines.append(
                videre.Text(
                    "Bulk operation — this cannot be undone from the app.",
                    color=videre.Colors.red,
                )
            )
        self.app.window.confirm(
            videre.Column(lines, space=4),
            "Send to trash",
            on_confirm=lambda: self._do_trash(paths),
        )

    def _do_trash(self, paths) -> None:
        ok, errors = self.context.trash_files(paths)
        trashed = set(paths) - {path for path, _ in errors}
        self._drop_paths(trashed)
        self._selected_files.clear()
        self._holder.control = self._scanned_state()
        if errors:
            self.app.window.alert(
                f"{ok} file(s) trashed, {len(errors)} failed.", "Send to trash"
            )

    def _drop_paths(self, trashed: set) -> None:
        for ext in list(self._result.others.keys()):
            kept = [f for f in self._result.others[ext] if str(f.path) not in trashed]
            if kept:
                self._result.others[ext] = kept
            else:
                del self._result.others[ext]
                if self._sel_ext == ext:
                    self._sel_ext = None

    def _open_folder(self, widget) -> None:
        if not self._selected_files:
            self.app.window.alert("Select at least one file first.", "Open folder")
            return
        folder = os.path.dirname(sorted(self._selected_files)[0])
        try:
            if sys.platform == "win32":
                os.startfile(folder)  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.run(["open", folder], check=False)
            else:
                subprocess.run(["xdg-open", folder], check=False)
        except Exception as exc:
            self.app.window.alert(f"{type(exc).__name__}: {exc}", "Open folder")
