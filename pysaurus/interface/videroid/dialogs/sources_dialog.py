"""Sources dialog — choose which videos to display.

Two "tabs" (videre has no Tabs widget, gap G2): a Simple checkbox tree and an
Advanced free-text expression, toggled by two buttons swapping a content holder.
"""

from __future__ import annotations

import videre
from videre.widgets.widget import Widget

from pysaurus.interface.videroid.widgets.tabs import Tabs

# (source-path key, human label) — keys mirror PySide6 SOURCE_TREE leaves.
_SOURCES = [
    ("readable.found.with_thumbnails", "Readable / Found / With thumbnails"),
    ("readable.found.without_thumbnails", "Readable / Found / Without thumbnails"),
    ("readable.not_found.with_thumbnails", "Readable / Not found / With thumbnails"),
    (
        "readable.not_found.without_thumbnails",
        "Readable / Not found / Without thumbnails",
    ),
    ("unreadable.found", "Unreadable / Found"),
    ("unreadable.not_found", "Unreadable / Not found"),
]
_VALID = "readable.found.with_thumbnails"


class SourcesDialog(videre.Column):
    __wprops__ = {}
    __slots__ = ("_checkboxes", "_expression", "_tabs")

    def __init__(self, current_sources=None, current_expression=None):
        self._checkboxes = {key: videre.Checkbox() for key, _ in _SOURCES}
        self._expression = videre.TextInput(str(current_expression or ""))
        self._load_current(current_sources or [])
        self._tabs = Tabs(
            [("Simple", self._simple_content), ("Advanced", self._advanced_content)]
        )
        super().__init__([self._tabs], space=8, expand_horizontal=True)

    def _load_current(self, current_sources) -> None:
        if not current_sources:
            self._checkboxes[_VALID].checked = True
            return
        for path in current_sources:
            prefix = ".".join(path)
            for key, checkbox in self._checkboxes.items():
                if key == prefix or key.startswith(prefix + "."):
                    checkbox.checked = True

    def _simple_content(self) -> Widget:
        rows = [
            videre.Row(
                [
                    self._checkboxes[key],
                    videre.Label(for_button=self._checkboxes[key], text=label),
                ],
                space=5,
                vertical_alignment=videre.Alignment.CENTER,
            )
            for key, label in _SOURCES
        ]
        rows.append(
            videre.Row(
                [
                    videre.Button("Select All", on_click=self._select_all),
                    videre.Button("Select None", on_click=self._select_none),
                    videre.Button("Valid Only", on_click=self._select_valid),
                ],
                space=5,
            )
        )
        return videre.Column(rows, space=4)

    def _advanced_content(self) -> Widget:
        return videre.Column(
            [
                videre.Text("Enter a search expression to filter videos:"),
                self._expression,
            ],
            space=4,
        )

    def _select_all(self, widget) -> None:
        for checkbox in self._checkboxes.values():
            checkbox.checked = True

    def _select_none(self, widget) -> None:
        for checkbox in self._checkboxes.values():
            checkbox.checked = False

    def _select_valid(self, widget) -> None:
        self._select_none(None)
        self._checkboxes[_VALID].checked = True

    def is_advanced(self) -> bool:
        return self._tabs.active_index == 1

    def get_sources(self) -> list[list[str]]:
        return [key.split(".") for key, cb in self._checkboxes.items() if cb.checked]

    def get_expression(self):
        return self._expression.value.strip() or None
