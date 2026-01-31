"""
Properties Page - Property types management.
"""

import logging
from typing import Any

from nicegui import ui

from pysaurus.interface.nicegui.api_bridge import api_bridge

logger = logging.getLogger(__name__)


# Property types supported
PROP_TYPES = [
    ("bool", "Boolean"),
    ("int", "Integer"),
    ("float", "Float"),
    ("str", "Text"),
]

DEFAULT_VALUES = {"bool": False, "int": 0, "float": 0.0, "str": ""}


class PropertiesPageState:
    """Local state for the properties page."""

    def __init__(self):
        self.definitions: list[dict[str, Any]] = []
        # Form state
        self.name: str = ""
        self.prop_type: str = "str"
        self.multiple: bool = False
        self.is_enumeration: bool = False
        self.default_value: str = ""
        self.enumeration_values: list[str] = []

    def load_data(self) -> None:
        """Load property types from backend."""
        try:
            self.definitions = api_bridge.describe_prop_types()
            logger.debug(f"Loaded {len(self.definitions)} property types")
        except Exception as e:
            logger.exception("Error loading property types")
            self.definitions = []
            ui.notify(f"Error loading properties: {e}", type="negative")

    def reset_form(self) -> None:
        """Reset the form to default values."""
        self.name = ""
        self.prop_type = "str"
        self.multiple = False
        self.is_enumeration = False
        self.default_value = ""
        self.enumeration_values = []


# Global page state
_page_state = PropertiesPageState()


def properties_page():
    """Render the properties page."""
    # Load initial data
    _page_state.load_data()

    with ui.column().classes("w-full h-full p-4"):
        # Header with back button
        with ui.row().classes("w-full items-center mb-4"):
            ui.button(
                icon="arrow_back", on_click=lambda: ui.navigate.to("/videos")
            ).props("flat")
            ui.label("Properties Management").classes(
                "text-2xl font-bold flex-1 text-center"
            )

        ui.separator()

        # Two-column layout
        with ui.row().classes("w-full gap-8 mt-4"):
            # Left: existing properties
            with ui.card().classes("flex-1"):
                _render_properties_list()

            # Right: create new property
            with ui.card().classes("w-96"):
                _render_create_form()


def _render_properties_list():
    """Render the list of existing properties."""
    ui.label("Current Properties").classes("text-xl font-bold mb-4")

    # Container for refreshable content
    list_container = ui.column().classes("w-full")

    def refresh_list():
        """Refresh the properties list."""
        _page_state.load_data()
        list_container.clear()

        with list_container:
            if _page_state.definitions:
                # Table header
                with ui.row().classes("w-full bg-gray-100 p-2 font-bold text-sm"):
                    ui.label("Name").classes("w-32")
                    ui.label("Type").classes("w-48")
                    ui.label("Default").classes("w-32")
                    ui.label("Actions").classes("flex-1")

                # Property rows
                for prop_def in _page_state.definitions:
                    _render_property_row(prop_def, refresh_list)
            else:
                ui.label("No properties defined").classes("text-gray-500 italic")

    refresh_list()


def _render_property_row(prop_def: dict[str, Any], refresh_callback):
    """Render a single property row."""
    name = prop_def.get("name", "")
    definition = prop_def.get("definition") or {}
    multiple = prop_def.get("multiple", False)

    # Extract type info from definition
    prop_type = definition.get("type", "str") if isinstance(definition, dict) else "str"
    enumeration = (
        definition.get("enumeration") if isinstance(definition, dict) else None
    )
    default_values = (
        definition.get("defaultValues", []) if isinstance(definition, dict) else []
    )

    with ui.row().classes("w-full p-2 border-b items-center hover:bg-gray-50"):
        # Name
        ui.label(name).classes("w-32 font-medium")

        # Type description
        with ui.element("div").classes("w-48"):
            type_desc = f"{'Multiple ' if multiple else ''}{prop_type}"
            ui.label(type_desc).classes("text-sm")
            if enumeration:
                enum_str = ", ".join(str(v) for v in enumeration[:3])
                if len(enumeration) > 3:
                    enum_str += f"... (+{len(enumeration) - 3})"
                ui.label(f"in {{{enum_str}}}").classes("text-xs text-gray-500")

        # Default values
        with ui.element("div").classes("w-32"):
            if default_values:
                default_str = ", ".join(str(v) for v in default_values)
                if multiple:
                    default_str = f"{{{default_str}}}"
                ui.label(default_str).classes("text-sm text-gray-600")
            else:
                ui.label("-").classes("text-gray-400")

        # Actions
        with ui.row().classes("flex-1 gap-1"):
            # Rename
            ui.button(
                icon="edit",
                on_click=lambda n=name: _rename_property_dialog(n, refresh_callback),
            ).props("flat dense round").tooltip("Rename")

            # Convert multiplicity
            if multiple:
                ui.button(
                    icon="looks_one",
                    on_click=lambda n=name: _convert_to_unique_dialog(
                        n, refresh_callback
                    ),
                ).props("flat dense round").tooltip("Convert to unique")
            else:
                ui.button(
                    icon="format_list_numbered",
                    on_click=lambda n=name: _convert_to_multiple_dialog(
                        n, refresh_callback
                    ),
                ).props("flat dense round").tooltip("Convert to multiple")

            # Delete
            ui.button(
                icon="delete",
                on_click=lambda n=name: _delete_property_dialog(n, refresh_callback),
            ).props("flat dense round color=negative").tooltip("Delete")


def _render_create_form():
    """Render the form to create a new property."""
    ui.label("Add New Property").classes("text-xl font-bold mb-4")

    # Name input
    name_input = ui.input("Property name", value=_page_state.name).classes("w-full")

    # Type select
    type_select = ui.select(
        {t[0]: t[1] for t in PROP_TYPES}, value=_page_state.prop_type, label="Type"
    ).classes("w-full")

    # Multiple checkbox
    multiple_checkbox = ui.checkbox(
        "Accept multiple values", value=_page_state.multiple
    )

    # Enumeration checkbox
    enum_checkbox = ui.checkbox("Is enumeration", value=_page_state.is_enumeration)

    # Default value / Enumeration values input
    default_container = ui.column().classes("w-full")

    def update_default_input():
        """Update the default value input based on settings."""
        default_container.clear()
        with default_container:
            if enum_checkbox.value:
                # Enumeration mode - allow adding multiple values
                ui.label("Enumeration values (comma-separated):").classes(
                    "text-sm text-gray-600"
                )
                enum_input = ui.input(placeholder="value1, value2, value3...").classes(
                    "w-full"
                )
                ui.label("First value is the default").classes("text-xs text-gray-500")
                return enum_input
            elif not multiple_checkbox.value:
                # Single default value
                prop_type = type_select.value
                if prop_type == "bool":
                    return ui.select(
                        {"false": "False", "true": "True"},
                        value="false",
                        label="Default value",
                    ).classes("w-full")
                elif prop_type == "int":
                    return ui.number("Default value", value=0).classes("w-full")
                elif prop_type == "float":
                    return ui.number("Default value", value=0.0, step=0.1).classes(
                        "w-full"
                    )
                else:  # str
                    return ui.input("Default value").classes("w-full")
            return None

    default_input = update_default_input()

    # Update when type/enumeration changes
    def on_type_change(e):
        nonlocal default_input
        default_input = update_default_input()

    def on_enum_change(e):
        nonlocal default_input
        default_input = update_default_input()

    type_select.on("change", on_type_change)
    enum_checkbox.on("change", on_enum_change)

    ui.separator().classes("my-4")

    # Buttons
    with ui.row().classes("w-full justify-end gap-2"):
        ui.button(
            "Reset",
            on_click=lambda: _reset_form(
                name_input, type_select, multiple_checkbox, enum_checkbox
            ),
        ).props("flat")

        ui.button(
            "Create",
            on_click=lambda: _create_property(
                name_input.value,
                type_select.value,
                multiple_checkbox.value,
                enum_checkbox.value,
                default_input,
            ),
        ).props("color=primary")


def _reset_form(name_input, type_select, multiple_checkbox, enum_checkbox):
    """Reset the form to default values."""
    name_input.value = ""
    type_select.value = "str"
    multiple_checkbox.value = False
    enum_checkbox.value = False


def _create_property(
    name: str, prop_type: str, multiple: bool, is_enum: bool, default_input
):
    """Create a new property."""
    if not name or not name.strip():
        ui.notify("Please enter a property name", type="warning")
        return

    name = name.strip()

    # Build definition based on settings
    try:
        if is_enum:
            # Parse enumeration values
            if (
                default_input
                and hasattr(default_input, "value")
                and default_input.value
            ):
                values_str = default_input.value
                values = [v.strip() for v in values_str.split(",") if v.strip()]
                if not values:
                    ui.notify(
                        "Please enter at least one enumeration value", type="warning"
                    )
                    return
                # Convert to proper type
                if prop_type == "int":
                    values = [int(v) for v in values]
                elif prop_type == "float":
                    values = [float(v) for v in values]
                elif prop_type == "bool":
                    values = [v.lower() in ("true", "1", "yes") for v in values]
                definition = values
            else:
                ui.notify("Please enter enumeration values", type="warning")
                return
        elif not multiple:
            # Single default value
            if default_input and hasattr(default_input, "value"):
                val = default_input.value
                if prop_type == "int":
                    definition = int(val) if val else 0
                elif prop_type == "float":
                    definition = float(val) if val else 0.0
                elif prop_type == "bool":
                    definition = val == "true"
                else:
                    definition = str(val) if val else ""
            else:
                definition = DEFAULT_VALUES.get(prop_type, "")
        else:
            # Multiple without enumeration - no default
            definition = None

        logger.info(
            f"Creating property: {name}, type={prop_type}, definition={definition}, multiple={multiple}"
        )

        result = api_bridge.create_prop_type(name, prop_type, definition, multiple)
        if result.get("error"):
            ui.notify(f"Error: {result['data']['message']}", type="negative")
        else:
            ui.notify(f"Property '{name}' created", type="positive")
            # Refresh page
            ui.navigate.to("/properties")

    except ValueError as e:
        ui.notify(f"Invalid value: {e}", type="negative")
    except Exception as e:
        logger.exception("Error creating property")
        ui.notify(f"Error: {e}", type="negative")


def _rename_property_dialog(name: str, refresh_callback):
    """Show dialog to rename a property."""
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Rename '{name}'").classes("text-lg font-bold")
        new_name_input = ui.input("New name", value=name).classes(
            "w-full min-w-[300px]"
        )

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Rename",
                on_click=lambda: _do_rename_property(
                    name, new_name_input.value, dialog, refresh_callback
                ),
            ).props("color=primary")

    dialog.open()


def _do_rename_property(old_name: str, new_name: str, dialog, refresh_callback):
    """Execute property rename."""
    if not new_name or new_name == old_name:
        dialog.close()
        return

    result = api_bridge.rename_prop_type(old_name, new_name)
    if result.get("error"):
        ui.notify(f"Error: {result['data']['message']}", type="negative")
    else:
        ui.notify(f"Renamed to '{new_name}'", type="positive")
        refresh_callback()

    dialog.close()


def _delete_property_dialog(name: str, refresh_callback):
    """Show confirmation dialog to delete a property."""
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Delete '{name}'?").classes("text-lg font-bold")
        ui.label("This will remove the property from all videos.").classes(
            "text-red-500"
        )

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Delete",
                on_click=lambda: _do_delete_property(name, dialog, refresh_callback),
            ).props("color=negative")

    dialog.open()


def _do_delete_property(name: str, dialog, refresh_callback):
    """Execute property deletion."""
    result = api_bridge.remove_prop_type(name)
    if result.get("error"):
        ui.notify(f"Error: {result['data']['message']}", type="negative")
    else:
        ui.notify(f"Property '{name}' deleted", type="positive")
        refresh_callback()

    dialog.close()


def _convert_to_unique_dialog(name: str, refresh_callback):
    """Show dialog to convert property to unique."""
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Convert '{name}' to unique?").classes("text-lg font-bold")
        ui.label("Videos with multiple values will keep only the first one.").classes(
            "text-orange-500"
        )

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Convert",
                on_click=lambda: _do_convert_multiplicity(
                    name, False, dialog, refresh_callback
                ),
            ).props("color=primary")

    dialog.open()


def _convert_to_multiple_dialog(name: str, refresh_callback):
    """Show dialog to convert property to multiple."""
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Convert '{name}' to multiple?").classes("text-lg font-bold")
        ui.label("This property will accept multiple values.").classes("text-gray-600")

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Convert",
                on_click=lambda: _do_convert_multiplicity(
                    name, True, dialog, refresh_callback
                ),
            ).props("color=primary")

    dialog.open()


def _do_convert_multiplicity(name: str, multiple: bool, dialog, refresh_callback):
    """Execute multiplicity conversion."""
    result = api_bridge.convert_prop_multiplicity(name, multiple)
    if result.get("error"):
        ui.notify(f"Error: {result['data']['message']}", type="negative")
    else:
        ui.notify(
            f"Property '{name}' converted to {'multiple' if multiple else 'unique'}",
            type="positive",
        )
        refresh_callback()

    dialog.close()
