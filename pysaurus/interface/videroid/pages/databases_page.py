"""Databases page — list / open / update / delete / create databases."""

from __future__ import annotations

import os

import videre
from videre.widgets.widget import Widget

from pysaurus.core.constants import VIDEO_SUPPORTED_EXTENSIONS
from pysaurus.interface.videroid import theme
from pysaurus.interface.videroid.pages.base_page import Page

# Item colors, matching the kyuti reference (databases_page.py:90-107).
# Expanded = blue (no hover change → stays blue). Collapsed = light gray that
# darkens on hover. Explicit hover/click are required, else videre's default
# Div hover (Colors.lightgray) would override the item's own background.
_EXPANDED_BORDER = "#1976d2"
_COLLAPSED_BG = "#f5f5f5"
_COLLAPSED_BORDER = "#dddddd"
_HOVER_BG = "#e8e8e8"
_HOVER_BORDER = "#bbbbbb"

_FOLDER = "\U0001f4c1"  # 📁
_FILE = "\U0001f4c4"  # 📄
_CROSS = "✕"  # ✕


class DatabasesPage(Page):
    title = "Databases"

    def __init__(self, app):
        super().__init__(app)
        self._sources: list[str] = []
        self._expanded: str | None = None
        # Persistent widgets (kept across refreshes; only their contents mutate).
        self._name_input = videre.TextInput(weight=1)
        self._db_column = videre.Column([], space=4)
        self._sources_column = videre.Column([], space=2)
        self._message = videre.Text("", color=videre.Colors.red, strong=True)

    # --- build (once) -------------------------------------------------------

    def build(self) -> Widget:
        left = videre.Column(
            [
                videre.Container(
                    videre.Text("Existing Databases", strong=True, size=20),
                    horizontal_alignment=videre.Alignment.CENTER,
                ),
                videre.Container(
                    videre.ScrollView(self._db_column),
                    border=videre.Border.all(1, videre.Colors.lightgray),
                    padding=videre.Padding.all(4),
                    weight=1,
                ),
            ],
            weight=1,
            space=5,
        )
        right = videre.Column(
            [
                videre.Container(
                    videre.Text("Create New Database", strong=True, size=20),
                    horizontal_alignment=videre.Alignment.CENTER,
                ),
                videre.Row(
                    [videre.Text("Name:"), self._name_input],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                ),
                videre.Text("Sources (folders and files):"),
                videre.Container(
                    videre.ScrollView(self._sources_column),
                    border=videre.Border.all(1, videre.Colors.lightgray),
                    padding=videre.Padding.all(4),
                    weight=1,
                ),
                videre.Row(
                    [
                        videre.Button("Add Folder", on_click=self._on_add_folder),
                        videre.Button("Add File", on_click=self._on_add_file),
                    ],
                    space=5,
                ),
                self._message,
                videre.Button("Create Database", on_click=self._on_create),
            ],
            weight=1,
            space=5,
        )
        self._populate_databases()
        self._populate_sources()
        return videre.Row([left, right], space=10)

    def on_show(self) -> None:
        self._populate_databases()

    # --- databases list -----------------------------------------------------

    def _populate_databases(self) -> None:
        names = self.context.get_database_names()
        self._db_column.controls = [self._db_item(n) for n in names] or [
            videre.Text("(no database yet)", italic=True)
        ]

    def _db_item(self, name: str) -> Widget:
        expanded = self._expanded == name
        if expanded:
            # Stays blue on hover (kyuti has no :hover rule for expanded items).
            bg = theme.SELECTED_BG
            border_color = _EXPANDED_BORDER
            hover_bg, hover_border = bg, border_color
        else:
            bg = videre.parse_color(_COLLAPSED_BG)
            border_color = _COLLAPSED_BORDER
            hover_bg = videre.parse_color(_HOVER_BG)
            hover_border = _HOVER_BORDER
        default_style = {
            "background_color": bg,
            "border": videre.Border.all(1, videre.parse_color(border_color)),
        }
        hover_style = {
            "background_color": hover_bg,
            "border": videre.Border.all(1, videre.parse_color(hover_border)),
        }
        header = videre.Div(
            videre.Text(name, strong=True),
            # Explicit hover + click, else videre's default gray Div hover wins.
            style={
                "default": default_style,
                "hover": hover_style,
                "click": hover_style,
            },
            data=name,
            on_click=self._on_toggle,
        )
        children = [header]
        if expanded:
            children.append(
                videre.Row(
                    [
                        videre.Button("Open", data=name, on_click=self._on_open),
                        videre.Button("Update", data=name, on_click=self._on_update),
                        videre.Button("Delete", data=name, on_click=self._on_delete),
                    ],
                    space=8,
                )
            )
        return videre.Column(children, space=2)

    def _on_toggle(self, widget: Widget) -> None:
        name = widget.data
        self._expanded = None if self._expanded == name else name
        self._populate_databases()

    def _on_open(self, widget: Widget) -> None:
        self._open(widget.data, False)

    def _on_update(self, widget: Widget) -> None:
        name = widget.data
        self.app.window.confirm(
            f"Open and update '{name}'?\n"
            "This will scan all sources and may take some time.",
            "Update Database",
            on_confirm=videre.Procedure(self._open, name, True),
        )

    def _open(self, name: str, update: bool) -> None:
        title = f"Updating '{name}'" if update else f"Opening '{name}'"
        self.app.run_process(
            title,
            videre.Procedure(self.context.open_database, name, update),
            self._after_database_ready,
            # Opening without an update just proceeds to the videos page (kyuti);
            # an update shows Continue so the user sees the scan result.
            autocontinue=not update,
        )

    def _after_database_ready(self, end) -> None:
        # On success a database is open -> show its videos; otherwise go back.
        self.app.show_page("videos" if self.context.has_database() else "databases")

    def _on_delete(self, widget: Widget) -> None:
        name = widget.data
        self.app.window.confirm(
            f"Are you sure you want to delete '{name}'?",
            "Delete Database",
            on_confirm=videre.Procedure(self._delete, name),
        )

    def _delete(self, name: str) -> None:
        self.context.delete_database(name)
        if self._expanded == name:
            self._expanded = None
        self._populate_databases()

    # --- sources (create form) ---------------------------------------------

    @staticmethod
    def _normalize(path: str) -> str:
        return os.path.normpath(os.path.abspath(path))

    def _on_add_folder(self, *args) -> None:
        self._add_source(videre.Dialog.select_directory())
        self._populate_sources()

    def _on_add_file(self, *args) -> None:
        skipped = 0
        for path in videre.Dialog.select_many_files():
            ext = os.path.splitext(path)[1].lstrip(".").lower()
            if ext in VIDEO_SUPPORTED_EXTENSIONS:
                self._add_source(path, announce=False)
            else:
                skipped += 1
        self._message.text = f"{skipped} non-video file(s) skipped." if skipped else ""
        self._populate_sources()

    def _add_source(self, path: str, announce: bool = True) -> None:
        if not path:
            return
        norm = self._normalize(path)
        if norm in {self._normalize(s) for s in self._sources}:
            if announce:
                self._message.text = "This path is already in the list."
        else:
            self._sources.append(norm)
            if announce:
                self._message.text = ""

    def _populate_sources(self) -> None:
        rows = []
        for source in self._sources:
            emoji = _FOLDER if os.path.isdir(source) else _FILE
            rows.append(
                videre.Row(
                    [
                        videre.Button(_CROSS, data=source, on_click=self._on_remove),
                        videre.Text(f"{emoji} {source}"),
                    ],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                )
            )
        self._sources_column.controls = rows or [
            videre.Text("(no source yet)", italic=True)
        ]

    def _on_remove(self, widget: Widget) -> None:
        source = widget.data
        self._sources = [s for s in self._sources if s != source]
        self._populate_sources()

    # --- create -------------------------------------------------------------

    def _on_create(self, *args) -> None:
        name = self._name_input.value.strip()
        if not name:
            self._message.text = "Please enter a database name."
            return
        if not self._sources:
            self._message.text = "Please add at least one source."
            return
        self.app.window.confirm(
            f"Create database '{name}' with {len(self._sources)} source(s)?\n"
            "This will scan all sources for video files.",
            "Create Database",
            on_confirm=videre.Procedure(self._create, name, list(self._sources)),
        )

    def _create(self, name: str, sources: list[str]) -> None:
        self._name_input.value = ""
        self._sources = []
        self._message.text = ""
        self._populate_sources()
        self.app.run_process(
            f"Creating '{name}'",
            videre.Procedure(self.context.create_database, name, sources, True),
            self._after_database_ready,
        )
