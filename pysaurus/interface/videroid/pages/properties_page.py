"""Properties page — manage custom property types.

Reference: kyuti/pages/properties_page.py. videre gaps worked around: no Table
(G1) → a `Column` of weighted `Row`s; no rich menu (G10) → an Actions ⚙
`ContextButton` per row. Manage Values / Move Values / Fill open dialogs
(phases 6.4 / 6.5); the rest (create, rename, convert, delete) is wired here.
"""

from __future__ import annotations

import videre
from videre.widgets.widget import Widget

from pysaurus.interface.videroid import theme
from pysaurus.interface.videroid.dialogs.fill_property_dialog import FillPropertyDialog
from pysaurus.interface.videroid.dialogs.move_values_dialog import MoveValuesDialog
from pysaurus.interface.videroid.dialogs.property_values_dialog import (
    PropertyValuesDialog,
)
from pysaurus.interface.videroid.pages.base_page import Page
from pysaurus.interface.videroid.widgets import table

_TYPES = ["str", "int", "float", "bool"]
# (title, layout weight) — shared by the header and the data rows so columns line up.
_COLS = [
    ("Name", 2),
    ("Type", 1),
    ("Default", 2),
    ("Multiple", 1),
    ("Enum", 3),
    ("Actions", 1),
]


class PropertiesPage(Page):
    title = "Properties"

    def __init__(self, app):
        super().__init__(app)
        self._table = videre.Column([], space=0)
        # Create-form widgets (built once, read on submit).
        self._name = videre.TextInput()
        self._type = videre.Dropdown(_TYPES)
        self._multiple = videre.Checkbox()
        self._use_enum = videre.Checkbox()
        self._enum = videre.TextInput()
        self._default = videre.TextInput()
        self._feedback = videre.Text("")

    # --- build --------------------------------------------------------------

    def build(self) -> Widget:
        left = videre.Column(
            [
                videre.Row(
                    [
                        videre.Text("Property Management", strong=True, weight=1),
                        videre.Button("Refresh", on_click=lambda w: self._reload()),
                    ],
                    vertical_alignment=videre.Alignment.CENTER,
                ),
                videre.Container(
                    videre.ScrollView(self._table, wrap_horizontal=True),
                    border=videre.Border.all(1, videre.Colors.lightgray),
                    weight=1,
                ),
                videre.Button("Fill with Terms…", on_click=self._on_fill),
            ],
            space=8,
            weight=1,
        )
        widget = videre.Row([left, self._create_form()], space=10)
        self._reload()
        return widget

    def on_show(self) -> None:
        self._reload()

    # --- table --------------------------------------------------------------

    def _prop_row(self, prop, index: int) -> Widget:
        enum = prop.enumeration
        if not enum:
            enum_text = "-"
        else:
            head = ", ".join(str(value) for value in enum[:3])
            enum_text = head + (f"… (+{len(enum) - 3})" if len(enum) > 3 else "")
        default = prop.default[0] if prop.default else ""
        actions = videre.ContextButton(
            "⚙", actions=self._prop_actions(prop), square=True
        )
        cells = [
            table.cell(prop.name, 2),
            table.cell(prop.type, 1),
            table.cell(default, 2),
            table.cell("Yes" if prop.multiple else "No", 1),
            table.cell(enum_text, 3),
            videre.Container(actions, weight=1, padding=videre.Padding.all(2)),
        ]
        return videre.Container(
            videre.Row(cells, space=0),
            background_color=theme.EVEN_BG if index % 2 else None,
        )

    def _reload(self) -> None:
        props = self.context.get_prop_types()
        rows: list[Widget] = [table.header(_COLS)]
        rows += [self._prop_row(prop, index) for index, prop in enumerate(props)]
        if not props:
            rows.append(
                videre.Container(
                    videre.Text("(no property defined)", italic=True),
                    padding=videre.Padding.all(6),
                )
            )
        self._table.controls = rows

    # --- per-property actions -----------------------------------------------

    def _prop_actions(self, prop):
        is_str = prop.type == "str"
        actions = []
        if is_str:
            actions.append(("Manage values…", lambda: self._manage_values(prop)))
        actions.append(("Rename…", lambda: self._rename(prop)))
        if is_str:
            label = (
                "Convert to single value"
                if prop.multiple
                else "Convert to multiple values"
            )
            actions.append((label, lambda: self._convert(prop)))
            if prop.multiple:
                actions.append(("Move values…", lambda: self._move_values(prop)))
        actions.append(("Delete", lambda: self._delete(prop)))
        return actions

    def _rename(self, prop) -> None:
        entry = videre.TextInput(prop.name)
        self.app.window.set_fancybox(
            videre.Column([videre.Text(f"Rename '{prop.name}' to:"), entry], space=8),
            title="Rename property",
            buttons=[
                videre.FancyCloseButton(
                    "Rename", on_click=lambda w: self._do_rename(prop, entry)
                ),
                videre.FancyCloseButton("Cancel"),
            ],
        )

    def _do_rename(self, prop, entry) -> None:
        new_name = entry.value.strip()
        if new_name and new_name != prop.name:
            self.context.rename_prop_type(prop.name, new_name)
            self._reload()

    def _convert(self, prop) -> None:
        message = (
            "Values will be merged into a single value."
            if prop.multiple
            else "Existing values will become lists."
        )
        self.app.window.confirm(
            f"Convert '{prop.name}'? {message}",
            "Convert property",
            on_confirm=lambda: self._do_convert(prop),
        )

    def _do_convert(self, prop) -> None:
        self.context.set_prop_type_multiple(prop.name, not prop.multiple)
        self._reload()

    def _delete(self, prop) -> None:
        self.app.window.confirm(
            f"Delete '{prop.name}'? This removes all its values from every video.",
            "Delete property",
            on_confirm=lambda: self._do_delete(prop),
        )

    def _do_delete(self, prop) -> None:
        self.context.delete_prop_type(prop.name)
        self._reload()

    # --- dialogs ------------------------------------------------------------

    def _manage_values(self, prop) -> None:
        dialog = PropertyValuesDialog(self.context, prop.name)
        self.app.window.set_fancybox(
            dialog,
            title=f"Manage values: {prop.name}",
            buttons=[videre.FancyCloseButton("Close")],
        )

    def _move_values(self, prop) -> None:
        dialog = MoveValuesDialog(self.context, prop)
        self.app.window.set_fancybox(
            dialog,
            title=f"Move values from {prop.name}",
            buttons=[
                videre.FancyCloseButton(
                    "Move", on_click=lambda w: self._do_move(prop, dialog)
                ),
                videre.FancyCloseButton("Cancel"),
            ],
        )

    def _do_move(self, prop, dialog) -> None:
        result = dialog.get_result()
        if result:
            values, target, concatenate = result
            self.context.move_property_values(
                values, prop.name, target.name, concatenate=concatenate
            )
            self._reload()

    def _on_fill(self, widget) -> None:
        dialog = FillPropertyDialog(self.context.get_prop_types())
        self.app.window.set_fancybox(
            dialog,
            title="Fill property with terms",
            buttons=[
                videre.FancyCloseButton(
                    "Fill", on_click=lambda w: self._do_fill(dialog)
                ),
                videre.FancyCloseButton("Cancel"),
            ],
        )

    def _do_fill(self, dialog) -> None:
        result = dialog.get_result()
        if result:
            prop, only_empty = result
            self.context.fill_property_with_terms(prop.name, only_empty=only_empty)
            self._reload()

    # --- create form --------------------------------------------------------

    def _create_form(self) -> Widget:
        return videre.Container(
            videre.Column(
                [
                    videre.Text("Create New Property", strong=True),
                    self._field("Name:", self._name),
                    self._field("Type:", self._type),
                    videre.Row(
                        [
                            self._multiple,
                            videre.Label(
                                for_button=self._multiple, text="Allow multiple (str)"
                            ),
                        ],
                        space=5,
                        vertical_alignment=videre.Alignment.CENTER,
                    ),
                    videre.Row(
                        [
                            self._use_enum,
                            videre.Label(
                                for_button=self._use_enum, text="Use enumeration (str)"
                            ),
                        ],
                        space=5,
                        vertical_alignment=videre.Alignment.CENTER,
                    ),
                    self._field("Enum (a, b, c):", self._enum),
                    self._field("Default:", self._default),
                    self._feedback,
                    videre.Row(
                        [
                            videre.Button("Reset", on_click=self._reset_form),
                            videre.Button("Create Property", on_click=self._on_create),
                        ],
                        space=5,
                    ),
                ],
                space=8,
            ),
            width=300,
            border=videre.Border.all(1, videre.Colors.lightgray),
            padding=videre.Padding.all(8),
        )

    def _field(self, label: str, widget: Widget) -> Widget:
        return videre.Row(
            [videre.Text(label), widget],
            space=5,
            vertical_alignment=videre.Alignment.CENTER,
        )

    def _reset_form(self, widget=None) -> None:
        self._name.value = ""
        self._enum.value = ""
        self._default.value = ""
        self._multiple.checked = False
        self._use_enum.checked = False
        self._feedback.text = ""

    def _on_create(self, widget) -> None:
        name = self._name.value.strip()
        if not name:
            self._feedback.text = "Please enter a property name."
            return
        prop_type = _TYPES[self._type.index]
        is_str = prop_type == "str"
        multiple = is_str and self._multiple.checked
        try:
            definition = self._parse_default(prop_type, self._default.value.strip())
        except ValueError:
            self._feedback.text = f"Invalid default value for type {prop_type}."
            return
        if is_str and self._use_enum.checked and self._enum.value.strip():
            definition = [v.strip() for v in self._enum.value.split(",") if v.strip()]
        try:
            self.context.create_prop_type(name, prop_type, definition, multiple)
        except Exception as exc:
            self._feedback.text = f"Failed to create property: {exc}"
            return
        self._reset_form()
        self._feedback.text = f"Property '{name}' created."
        self._reload()

    def _parse_default(self, prop_type: str, text: str):
        if prop_type == "bool":
            return text.lower() in ("true", "1", "yes")
        if prop_type == "int":
            return int(text) if text else 0
        if prop_type == "float":
            return float(text) if text else 0.0
        return text
