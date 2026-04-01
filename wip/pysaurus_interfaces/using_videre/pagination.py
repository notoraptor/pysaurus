from typing import Callable

import videre


class Pagination(videre.Row):
    __wprops__ = {}
    __slots__ = ("_on_change", "_page_number", "_nb_pages")

    def __init__(
        self, nb_pages: int, page_number: int, on_change: Callable[[int], None]
    ):
        self._on_change = on_change
        self._page_number = page_number
        self._nb_pages = nb_pages
        super().__init__(
            [
                videre.Button("<<", on_click=self._on_first, disabled=page_number == 0),
                videre.Button(
                    "<", on_click=self._on_previous, disabled=page_number == 0
                ),
                videre.Text(f"Page {page_number + 1}/{nb_pages}"),
                videre.Button(
                    ">", on_click=self._on_next, disabled=page_number == nb_pages - 1
                ),
                videre.Button(
                    ">>", on_click=self._on_last, disabled=page_number == nb_pages - 1
                ),
            ],
            vertical_alignment=videre.Alignment.CENTER,
            space=10,
        )

    def _on_first(self, *args):
        if self._page_number != 0:
            self._on_change(0)

    def _on_last(self, *args):
        if self._page_number != self._nb_pages - 1:
            self._on_change(self._nb_pages - 1)

    def _on_previous(self, *args):
        if self._page_number > 0:
            self._on_change(self._page_number - 1)

    def _on_next(self, *args):
        if self._page_number < self._nb_pages - 1:
            self._on_change(self._page_number + 1)
