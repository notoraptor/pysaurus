"""Lightweight tab strip — videre has no Tabs widget (gap G2).

A row of buttons over a content holder: clicking a tab rebuilds its content from
the matching builder. Factors out the duplicated "buttons + holder + swap"
pattern of the Files page and the Sources dialog.

Each tab is a ``(label, builder)`` pair where ``builder()`` returns the tab's
content. Builders are called lazily — on construction for the first tab, then on
every switch and on every :meth:`refresh` — so the content always reflects the
caller's current state (e.g. the Files page rebuilds the active tab after the
selected extension changes).
"""

from __future__ import annotations

from typing import Callable

import videre
from videre.widgets.widget import Widget


class Tabs(videre.Column):
    __wprops__ = {}
    __slots__ = ("_builders", "_holder", "_active")

    def __init__(
        self, tabs: list[tuple[str, Callable[[], Widget]]], *, fill: bool = False
    ):
        self._builders = [builder for _, builder in tabs]
        self._active = 0
        weight = 1 if fill else 0
        self._holder = videre.Container(weight=weight)
        self._holder.control = self._builders[0]()
        buttons = videre.Row(
            [
                videre.Button(label, data=index, on_click=self._on_click)
                for index, (label, _) in enumerate(tabs)
            ],
            space=4,
        )
        super().__init__(
            [buttons, self._holder], space=8, weight=weight, expand_horizontal=True
        )

    def _on_click(self, button) -> None:
        self._active = button.data
        self.refresh()

    def refresh(self) -> None:
        """Rebuild the active tab's content (e.g. after the caller's state changed)."""
        self._holder.control = self._builders[self._active]()

    @property
    def active_index(self) -> int:
        return self._active
