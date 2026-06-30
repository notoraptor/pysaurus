"""Grouping dialog — choose how to group videos.

Shown as fancybox content. The PySide6 "type combo + dependent field combo" is
flattened into a single field dropdown (attributes + properties, the latter
marked), avoiding a dynamic repopulation. Returns a grouping dict.
"""

from __future__ import annotations

import videre

from pysaurus.interface.common.common import FIELD_MAP

_SORT_KEYS = ["field", "count", "length"]
_SORT_LABELS = ["By field value", "By video count", "By field value length"]


class GroupingDialog(videre.Column):
    __wprops__ = {}
    __slots__ = ("_options", "_field", "_sort", "_reverse", "_singletons")

    def __init__(self, property_names, current=None):
        # Each option: (label, field_name, is_property).
        self._options = [(f.title, f.name, False) for f in FIELD_MAP.allowed]
        self._options += [(f"{name} (property)", name, True) for name in property_names]
        self._field = videre.Dropdown([label for label, _, _ in self._options])
        self._sort = videre.Dropdown(list(_SORT_LABELS))
        self._reverse = videre.Checkbox()
        # Default unchecked, mirroring pyside6 (singletons hidden by default).
        self._singletons = videre.Checkbox()

        if current is not None and getattr(current, "field", None):
            for index, (_, name, is_prop) in enumerate(self._options):
                if name == current.field and is_prop == bool(current.is_property):
                    self._field.index = index
                    break
            if current.sorting in _SORT_KEYS:
                self._sort.index = _SORT_KEYS.index(current.sorting)
            self._reverse.checked = bool(current.reverse)
            self._singletons.checked = bool(current.allow_singletons)

        super().__init__(
            [
                videre.Row(
                    [videre.Text("Group by:"), self._field],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                ),
                videre.Row(
                    [videre.Text("Sort groups:"), self._sort],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                ),
                videre.Row(
                    [
                        self._reverse,
                        videre.Label(for_button=self._reverse, text="Reverse order"),
                    ],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                ),
                videre.Row(
                    [
                        self._singletons,
                        videre.Label(
                            for_button=self._singletons, text="Allow singletons"
                        ),
                    ],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                ),
            ],
            space=8,
            expand_horizontal=True,
        )

    def get_result(self) -> dict:
        _, name, is_prop = self._options[self._field.index]
        return {
            "field": name,
            "is_property": is_prop,
            "sorting": _SORT_KEYS[self._sort.index],
            "reverse": self._reverse.checked,
            "allow_singletons": self._singletons.checked,
        }
