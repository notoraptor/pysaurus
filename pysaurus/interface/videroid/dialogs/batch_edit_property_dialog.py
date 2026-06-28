"""Batch-edit-property dialog — edit ONE property across N selected videos.

Shown as fancybox content (the active batch path from the Videos selection menu's
"Edit property: ..."). Three columns — *To remove* / *Current* / *To add* — let
the user compute the final `(to_add, to_remove)` applied to the whole selection.

videre gaps worked around: no Table (G1) → three `Column`s in a `Row`; no SpinBox
(G5) → `TextInput` + validation for int/float; `Dropdown` for enum/bool.
"""

from __future__ import annotations

import videre
from videre.widgets.widget import Widget


class BatchEditPropertyDialog(videre.Column):
    __wprops__ = {}
    __slots__ = (
        "_prop",
        "_counts",
        "_current",
        "_to_add",
        "_to_remove",
        "_editor",
        "_holder",
        "_error",
    )

    def __init__(self, prop, nb_videos: int, values_and_counts):
        self._prop = prop
        self._counts = {value: count for value, count in (values_and_counts or [])}
        self._current = sorted(self._counts, key=lambda v: (-self._counts[v], str(v)))
        self._to_add: list = []
        self._to_remove: list = []
        self._editor = self._make_editor()
        self._holder = videre.Container()
        self._error = videre.Text("", color=videre.Colors.red)
        kind = "multiple" if prop.multiple else "single"
        super().__init__(
            [
                videre.Text(
                    f'Edit "{prop.name}" ({kind}) for {nb_videos} video(s)', strong=True
                ),
                self._holder,
                videre.Row(
                    [
                        videre.Text("New value:"),
                        self._editor,
                        videre.Button("Add", on_click=self._on_add_new),
                    ],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                ),
                self._error,
            ],
            space=8,
            expand_horizontal=True,
        )
        self._render()

    # --- per-type new-value editor ------------------------------------------

    def _make_editor(self) -> Widget:
        enum = getattr(self._prop, "enumeration", None)
        if enum:
            return videre.Dropdown([str(value) for value in enum])
        if self._prop.type == "bool":
            return videre.Dropdown(["true", "false"])
        return videre.TextInput()

    def _read_new_value(self):
        enum = getattr(self._prop, "enumeration", None)
        if self._prop.type == "bool":
            return self._editor.selected == "true"
        text = (self._editor.selected if enum else self._editor.value) or ""
        text = text.strip()
        if not text:
            return None
        try:
            if self._prop.type == "int":
                return int(text)
            if self._prop.type == "float":
                return float(text)
        except ValueError:
            return None
        return text

    # --- rendering ----------------------------------------------------------

    def _column(self, title: str, rows: list[Widget]) -> Widget:
        return videre.Container(
            videre.Column(
                [
                    videre.Text(title, strong=True),
                    videre.Container(
                        videre.ScrollView(
                            videre.Column(
                                rows or [videre.Text("(none)", italic=True)], space=2
                            ),
                            wrap_horizontal=True,
                        ),
                        height=200,
                    ),
                ],
                space=4,
            ),
            border=videre.Border.all(1, videre.Colors.lightgray),
            padding=videre.Padding.all(4),
            weight=1,
        )

    def _render(self) -> None:
        remove_rows = [
            videre.Row(
                [
                    videre.Text(str(value), weight=1),
                    videre.Button("→ Restore", data=value, on_click=self._restore),
                ],
                space=5,
                vertical_alignment=videre.Alignment.CENTER,
            )
            for value in self._to_remove
        ]
        current_rows = [
            videre.Row(
                [
                    videre.Button("← Remove", data=value, on_click=self._remove),
                    videre.Text(f"{value} ({self._counts.get(value, 0)})", weight=1),
                    videre.Button("→ Add", data=value, on_click=self._add_existing),
                ],
                space=5,
                vertical_alignment=videre.Alignment.CENTER,
            )
            for value in self._current
        ]
        add_rows = [
            videre.Row(
                [
                    videre.Text(
                        f"{value} ({self._counts[value]})"
                        if value in self._counts
                        else f"{value} (new)",
                        weight=1,
                    ),
                    videre.Button("← Cancel", data=value, on_click=self._cancel_add),
                ],
                space=5,
                vertical_alignment=videre.Alignment.CENTER,
            )
            for value in self._to_add
        ]
        bulk = [
            videre.Button("Restore all", on_click=self._restore_all),
            videre.Button("Remove all", on_click=self._remove_all),
        ]
        if self._prop.multiple:
            bulk.append(videre.Button("Add all", on_click=self._add_all))
        bulk.append(videre.Button("Cancel all", on_click=self._cancel_all))
        self._holder.control = videre.Column(
            [
                videre.Row(
                    [
                        self._column("To remove", remove_rows),
                        self._column("Current", current_rows),
                        self._column("To add", add_rows),
                    ],
                    space=6,
                ),
                videre.Row(bulk, space=4),
            ],
            space=6,
        )

    # --- state transitions --------------------------------------------------

    def _remove(self, widget: Widget) -> None:
        value = widget.data
        if value in self._current:
            self._current.remove(value)
            self._to_remove.append(value)
            self._render()

    def _restore(self, widget: Widget) -> None:
        value = widget.data
        if value in self._to_remove:
            self._to_remove.remove(value)
            self._current.append(value)
            self._render()

    def _add_existing(self, widget: Widget) -> None:
        self._promote(widget.data)

    def _cancel_add(self, widget: Widget) -> None:
        value = widget.data
        if value in self._to_add:
            self._to_add.remove(value)
            if value in self._counts and value not in self._current:
                self._current.append(value)
            self._render()

    def _on_add_new(self, widget: Widget) -> None:
        value = self._read_new_value()
        if value is None:
            self._error.text = f"Invalid value for type {self._prop.type}."
            return
        self._error.text = ""
        self._promote(value)

    def _promote(self, value) -> None:
        """Move a value to 'To add'. Single-value props replace everything."""
        if not self._prop.multiple:
            self._to_add = [value]
            self._to_remove = [v for v in self._counts if v != value]
            self._current = []
            self._render()
            return
        if value in self._to_remove:
            self._to_remove.remove(value)
        if value in self._current:
            self._current.remove(value)
        if value not in self._to_add:
            self._to_add.append(value)
        self._render()

    def _remove_all(self, widget: Widget) -> None:
        self._to_remove.extend(self._current)
        self._current = []
        self._render()

    def _restore_all(self, widget: Widget) -> None:
        self._current.extend(self._to_remove)
        self._to_remove = []
        self._render()

    def _add_all(self, widget: Widget) -> None:
        for value in self._current:
            if value not in self._to_add:
                self._to_add.append(value)
        self._current = []
        self._render()

    def _cancel_all(self, widget: Widget) -> None:
        for value in self._to_add:
            if value in self._counts and value not in self._current:
                self._current.append(value)
        self._to_add = []
        self._render()

    def get_changes(self) -> tuple[list, list]:
        return list(self._to_add), list(self._to_remove)
