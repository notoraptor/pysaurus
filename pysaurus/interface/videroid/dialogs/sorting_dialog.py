"""Sorting dialog — edit the multi-level sort order.

Shown as fancybox content. Drag-reorder (videre gap G8) is replaced by Move
Up/Down buttons. Returns the sorting as a list of "+field"/"-field" strings.
"""

from __future__ import annotations

import videre
from videre.widgets.widget import Widget

from pysaurus.interface.common.common import FIELD_MAP


class SortingDialog(videre.Column):
    __wprops__ = {}
    __slots__ = ("_criteria", "_list", "_dropdown", "_title_to_name")

    def __init__(self, sorting: list[str]):
        self._criteria: list[list] = []
        for item in sorting:
            reverse = item.startswith("-")
            field = item[1:] if item[:1] in "+-" else item
            self._criteria.append([field, reverse])
        sortable = list(FIELD_MAP.sortable)
        self._title_to_name = {f.title: f.name for f in sortable}
        self._list = videre.Column([], space=2)
        self._dropdown = videre.Dropdown([f.title for f in sortable])
        super().__init__(
            [
                videre.Text("Sort by (first has highest priority):"),
                videre.Container(
                    videre.ScrollView(self._list, wrap_horizontal=True),
                    border=videre.Border.all(1, videre.Colors.lightgray),
                    padding=videre.Padding.all(4),
                    weight=1,
                ),
                videre.Row(
                    [
                        self._dropdown,
                        videre.Button("Add ↑", on_click=self._add_asc),
                        videre.Button("Add ↓", on_click=self._add_desc),
                    ],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                ),
            ],
            space=8,
            expand_horizontal=True,
        )
        self._populate()

    def _populate(self) -> None:
        rows: list[Widget] = []
        for index, (field, reverse) in enumerate(self._criteria):
            info = FIELD_MAP.fields.get(field)
            rows.append(
                videre.Row(
                    [
                        videre.Button("↑", data=index, on_click=self._up),
                        videre.Button("↓", data=index, on_click=self._down),
                        videre.Button(
                            "▼" if reverse else "▲", data=index, on_click=self._toggle
                        ),
                        videre.Text(info.title if info else field, weight=1),
                        videre.Button("✕", data=index, on_click=self._remove),
                    ],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                )
            )
        self._list.controls = rows or [videre.Text("(no sort criterion)", italic=True)]

    def _up(self, widget: Widget) -> None:
        i = widget.data
        if i > 0:
            self._criteria[i - 1], self._criteria[i] = (
                self._criteria[i],
                self._criteria[i - 1],
            )
            self._populate()

    def _down(self, widget: Widget) -> None:
        i = widget.data
        if i < len(self._criteria) - 1:
            self._criteria[i + 1], self._criteria[i] = (
                self._criteria[i],
                self._criteria[i + 1],
            )
            self._populate()

    def _toggle(self, widget: Widget) -> None:
        self._criteria[widget.data][1] = not self._criteria[widget.data][1]
        self._populate()

    def _remove(self, widget: Widget) -> None:
        del self._criteria[widget.data]
        self._populate()

    def _add(self, reverse: bool) -> None:
        name = self._title_to_name.get(self._dropdown.selected)
        if name and all(field != name for field, _ in self._criteria):
            self._criteria.append([name, reverse])
            self._populate()

    def _add_asc(self, widget: Widget) -> None:
        self._add(False)

    def _add_desc(self, widget: Widget) -> None:
        self._add(True)

    def get_result(self) -> list[str]:
        return [
            f"-{field}" if reverse else f"+{field}" for field, reverse in self._criteria
        ]
