"""Fill property dialog — pick a (str, multiple) property to fill with terms
extracted from filenames. Passive: returns (prop_type, only_empty) on OK.
Reference: kyuti/dialogs/fill_property_dialog.py.
"""

from __future__ import annotations

import videre


class FillPropertyDialog(videre.Column):
    __wprops__ = {}
    __slots__ = ("_eligible", "_combo", "_only_empty")

    def __init__(self, prop_types):
        self._eligible = [
            prop for prop in prop_types if prop.type == "str" and prop.multiple
        ]
        labels = [prop.name for prop in self._eligible] or ["(no eligible property)"]
        self._combo = videre.Dropdown(labels)
        # Default unchecked, mirroring kyuti (fill all videos by default).
        self._only_empty = videre.Checkbox()
        children = [
            videre.Row(
                [videre.Text("Property:"), self._combo],
                space=5,
                vertical_alignment=videre.Alignment.CENTER,
            ),
            videre.Row(
                [
                    self._only_empty,
                    videre.Label(
                        for_button=self._only_empty,
                        text="Only fill videos without values",
                    ),
                ],
                space=5,
                vertical_alignment=videre.Alignment.CENTER,
            ),
        ]
        if not self._eligible:
            children.append(
                videre.Text(
                    "No eligible property (needs a str, multiple property).",
                    color=videre.Colors.red,
                )
            )
        super().__init__(children, space=8, expand_horizontal=True)

    def get_result(self):
        if not self._eligible:
            return None
        return self._eligible[self._combo.index], self._only_empty.checked
