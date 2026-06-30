"""Property values dialog — manage all values of one property (immediate actions).

Reference: kyuti/dialogs/property_values_dialog.py. Actions apply right away
(Close-only dialog). videre gap G-MODAL (single fancybox, no stacked modals):
confirmations/rename happen INLINE in a prompt row instead of nested fancyboxes.
"""

from __future__ import annotations

from collections import Counter

import videre

from pysaurus.properties.property_value_modifier import PropertyValueModifier


class PropertyValuesDialog(videre.Column):
    __wprops__ = {}
    __slots__ = ("_context", "_prop", "_list", "_stats", "_prompt", "_selected")

    def __init__(self, context, prop_name: str):
        self._context = context
        self._prop = prop_name
        self._selected: set = set()
        self._list = videre.Column([], space=2)
        self._stats = videre.Text("")
        self._prompt = videre.Container()
        modifier_buttons = [
            videre.Button(name, data=name, on_click=self._ask_modifier)
            for name in PropertyValueModifier.get_modifiers()
        ]
        super().__init__(
            [
                self._stats,
                videre.Container(
                    videre.ScrollView(self._list, wrap_horizontal=True),
                    height=280,
                    border=videre.Border.all(1, videre.Colors.lightgray),
                    padding=videre.Padding.all(4),
                ),
                videre.Row(
                    [
                        videre.Button("Delete Selected", on_click=self._ask_delete),
                        videre.Button("Rename Value…", on_click=self._ask_rename),
                        *modifier_buttons,
                    ],
                    space=5,
                ),
                self._prompt,
            ],
            space=8,
            expand_horizontal=True,
        )
        self._reload()

    def _reload(self) -> None:
        data = self._context.get_property_values(self._prop)  # {video_id: [values]}
        counter: Counter = Counter()
        for values in data.values():
            counter.update(values)
        total = sum(counter.values())
        self._stats.text = f"{len(counter)} unique values / {total} total usages"
        self._selected.clear()
        self._prompt.control = None
        rows = [
            videre.Row(
                [
                    videre.Checkbox(data=value, on_change=self._on_check),
                    videre.Text(f"{value} ({count})", weight=1),
                ],
                space=5,
                vertical_alignment=videre.Alignment.CENTER,
            )
            for value, count in sorted(
                counter.items(), key=lambda kv: (-kv[1], str(kv[0]))
            )
        ]
        self._list.controls = rows or [videre.Text("(no value)", italic=True)]

    def _on_check(self, checkbox) -> None:
        if checkbox.checked:
            self._selected.add(checkbox.data)
        else:
            self._selected.discard(checkbox.data)

    # --- inline prompt (G-MODAL workaround) ---------------------------------

    def _clear_prompt(self, *args) -> None:
        self._prompt.control = None

    def _confirm(self, message: str, on_yes) -> None:
        def yes(widget):
            on_yes()

        self._prompt.control = videre.Row(
            [
                videre.Text(message, weight=1),
                videre.Button("Yes", on_click=yes),
                videre.Button("No", on_click=self._clear_prompt),
            ],
            space=5,
            vertical_alignment=videre.Alignment.CENTER,
        )

    def _ask_delete(self, widget) -> None:
        if not self._selected:
            return
        values = list(self._selected)
        self._confirm(
            f"Delete {len(values)} value(s)?", lambda: self._do_delete(values)
        )

    def _do_delete(self, values) -> None:
        self._context.delete_property_values(self._prop, values)
        self._reload()

    def _ask_modifier(self, widget) -> None:
        modifier = widget.data
        self._confirm(
            f"Apply '{modifier}' to ALL values?", lambda: self._do_modifier(modifier)
        )

    def _do_modifier(self, modifier) -> None:
        self._context.apply_on_prop_value(self._prop, modifier)
        self._reload()

    def _ask_rename(self, widget) -> None:
        if len(self._selected) != 1:
            self._prompt.control = videre.Text(
                "Select exactly one value to rename.", color=videre.Colors.red
            )
            return
        old = next(iter(self._selected))
        entry = videre.TextInput(str(old))
        self._prompt.control = videre.Row(
            [
                videre.Text("Rename to:"),
                entry,
                videre.Button("Apply", on_click=lambda w: self._do_rename(old, entry)),
                videre.Button("Cancel", on_click=self._clear_prompt),
            ],
            space=5,
            vertical_alignment=videre.Alignment.CENTER,
        )

    def _do_rename(self, old, entry) -> None:
        new_value = entry.value.strip()
        if new_value and new_value != str(old):
            self._context.replace_property_values(self._prop, [old], new_value)
        self._reload()
