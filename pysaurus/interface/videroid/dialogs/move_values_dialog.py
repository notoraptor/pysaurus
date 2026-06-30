"""Move values dialog — move selected values from a str-multiple property to
another str property. Passive: returns (values, target_prop, concatenate) on OK.
Reference: kyuti/dialogs/move_values_dialog.py.
"""

from __future__ import annotations

from collections import Counter

import videre


class MoveValuesDialog(videre.Column):
    __wprops__ = {}
    __slots__ = ("_targets", "_values", "_selected", "_list", "_target", "_concat")

    def __init__(self, context, source_prop):
        data = context.get_property_values(source_prop.name)  # {video_id: [values]}
        counter: Counter = Counter()
        for values in data.values():
            counter.update(values)
        self._values = sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0])))
        self._selected: set = set()
        self._targets = [
            prop
            for prop in context.get_prop_types()
            if prop.type == "str" and prop.name != source_prop.name
        ]
        self._list = videre.Column([], space=2)
        target_labels = [
            f"{prop.name} ({'multiple' if prop.multiple else 'single'})"
            for prop in self._targets
        ] or ["(no target property)"]
        self._target = videre.Dropdown(target_labels)
        self._concat = videre.Checkbox()
        super().__init__(
            [
                videre.Text(f"Move values from '{source_prop.name}':"),
                videre.Container(
                    videre.ScrollView(self._list, wrap_horizontal=True),
                    height=240,
                    border=videre.Border.all(1, videre.Colors.lightgray),
                    padding=videre.Padding.all(4),
                ),
                videre.Row(
                    [videre.Text("Move to:"), self._target],
                    space=5,
                    vertical_alignment=videre.Alignment.CENTER,
                ),
                videre.Row(
                    [
                        self._concat,
                        videre.Label(
                            for_button=self._concat, text="Concatenate into one value"
                        ),
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
        rows = [
            videre.Row(
                [
                    videre.Checkbox(data=value, on_change=self._on_check),
                    videre.Text(f"{value} ({count})", weight=1),
                ],
                space=5,
                vertical_alignment=videre.Alignment.CENTER,
            )
            for value, count in self._values
        ]
        self._list.controls = rows or [videre.Text("(no value)", italic=True)]

    def _on_check(self, checkbox) -> None:
        if checkbox.checked:
            self._selected.add(checkbox.data)
        else:
            self._selected.discard(checkbox.data)

    def get_result(self):
        if not self._targets or not self._selected:
            return None
        target = self._targets[self._target.index]
        return list(self._selected), target, self._concat.checked
