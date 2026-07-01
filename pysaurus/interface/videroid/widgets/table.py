"""Lightweight table helpers — videre has no Table widget (gap G1).

A "table" in videroid is a ``Column`` of weighted ``Row``s. These two helpers
factor out the header row and the text cell that were copy-pasted across the
Properties and Files pages. Each page keeps its own row wrapper (zebra striping
vs selection highlight) and any non-text cells (buttons, ⚙ menus) built inline,
since those differ from table to table.
"""

from __future__ import annotations

import videre
from videre.widgets.widget import Widget

from pysaurus.interface.videroid import theme


def cell(
    text,
    weight: int = 1,
    strong: bool = False,
    color=None,
    align: videre.Alignment = videre.Alignment.START,
) -> Widget:
    """A text cell spanning ``weight`` columns (``align`` = END to right-align)."""
    return videre.Container(
        videre.Text(str(text), strong=strong, wrap=videre.TextWrap.WORD, color=color),
        weight=weight,
        padding=videre.Padding.axis(vertical=4, horizontal=6),
        horizontal_alignment=align,
    )


def header(columns) -> Widget:
    """A header row from ``columns`` = list of ``(title, weight)`` pairs."""
    return videre.Container(
        videre.Row(
            [cell(title, weight, strong=True) for title, weight in columns], space=0
        ),
        background_color=theme.HEADER_BG,
    )
