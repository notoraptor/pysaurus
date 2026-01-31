"""
Databases Page - Database selection and creation.
"""

import logging

from nicegui import ui

from pysaurus.interface.nicegui.api_bridge import api_bridge
from pysaurus.interface.nicegui.state import app_state

logger = logging.getLogger(__name__)


def databases_page():
    """Render the databases page."""
    with ui.column().classes("w-full max-w-4xl mx-auto p-4 gap-4"):
        ui.label("Pysaurus").classes("text-4xl font-bold text-center mb-4")
        ui.label("Video Collection Manager").classes("text-xl text-gray-500 text-center mb-8")

        # Two-column layout
        with ui.row().classes("w-full gap-8"):
            # Left column: Existing databases
            with ui.card().classes("flex-1"):
                _render_existing_databases()

            # Right column: Create new database
            with ui.card().classes("flex-1"):
                _render_create_database()


def _render_existing_databases():
    """Render the existing databases section."""
    ui.label("Open Database").classes("text-xl font-bold mb-4")

    # Container for database list (will be refreshed)
    databases_container = ui.column().classes("w-full gap-2")

    def refresh_databases():
        """Refresh the database list."""
        databases_container.clear()
        with databases_container:
            try:
                databases = api_bridge.get_database_names()
                if databases:
                    for db_name in databases:
                        _render_database_item(db_name, refresh_databases)
                else:
                    ui.label("No databases found").classes("text-gray-500 italic")
            except Exception as e:
                logger.exception("Error loading databases")
                ui.label(f"Error: {e}").classes("text-red-500")

    refresh_databases()


def _render_database_item(db_name: str, refresh_callback):
    """Render a single database item."""
    with ui.row().classes("w-full items-center justify-between p-2 hover:bg-gray-100 rounded"):
        # Database name
        ui.label(db_name).classes("flex-1 font-medium")

        # Action buttons
        with ui.row().classes("gap-1"):
            # Open with update
            ui.button(
                icon="refresh",
                on_click=lambda name=db_name: _open_database(name, update=True),
            ).props("flat dense round color=primary").tooltip("Open and update")

            # Open read-only (no update)
            ui.button(
                icon="folder_open",
                on_click=lambda name=db_name: _open_database(name, update=False),
            ).props("flat dense round").tooltip("Open (read-only)")

            # Rename
            ui.button(
                icon="edit",
                on_click=lambda name=db_name: _rename_database_dialog(name, refresh_callback),
            ).props("flat dense round").tooltip("Rename")

            # Delete
            ui.button(
                icon="delete",
                on_click=lambda name=db_name: _delete_database_dialog(name, refresh_callback),
            ).props("flat dense round color=negative").tooltip("Delete")


def _open_database(name: str, update: bool = True):
    """Open a database and navigate to home page.

    Args:
        name: Database name
        update: If True, scan folders and update database. If False, open read-only.
    """
    logger.info(f"Opening database: {name} (update={update})")
    app_state.database_name = name
    app_state.reset_view()

    # Call API to open database (runs in background thread)
    result = api_bridge.open_database(name, update=update)
    if result.get("error"):
        ui.notify(f"Error: {result['data']['message']}", type="negative")
    else:
        # Always navigate to home page to wait for DatabaseReady notification
        ui.navigate.to("/home")


def _rename_database_dialog(name: str, refresh_callback):
    """Show dialog to rename a database."""
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Rename '{name}'").classes("text-lg font-bold")
        new_name_input = ui.input("New name", value=name).classes("w-full")

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Rename",
                on_click=lambda: _do_rename_database(
                    name, new_name_input.value, dialog, refresh_callback
                ),
            ).props("color=primary")

    dialog.open()


def _do_rename_database(old_name: str, new_name: str, dialog, refresh_callback):
    """Execute database rename."""
    if not new_name or new_name == old_name:
        dialog.close()
        return

    # Need to open database first to rename it
    api_bridge.open_database(old_name, update=False)
    result = api_bridge.rename_database(new_name)
    api_bridge.close_database()

    if result.get("error"):
        ui.notify(f"Error: {result['data']['message']}", type="negative")
    else:
        ui.notify(f"Renamed to '{new_name}'", type="positive")
        refresh_callback()

    dialog.close()


def _delete_database_dialog(name: str, refresh_callback):
    """Show confirmation dialog to delete a database."""
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Delete '{name}'?").classes("text-lg font-bold")
        ui.label("This action cannot be undone.").classes("text-red-500")

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Delete",
                on_click=lambda: _do_delete_database(name, dialog, refresh_callback),
            ).props("color=negative")

    dialog.open()


def _do_delete_database(name: str, dialog, refresh_callback):
    """Execute database deletion."""
    # Need to open database first to delete it
    api_bridge.open_database(name, update=False)
    result = api_bridge.delete_database()

    if result.get("error"):
        ui.notify(f"Error: {result['data']['message']}", type="negative")
    else:
        ui.notify(f"Deleted '{name}'", type="positive")
        refresh_callback()

    dialog.close()


def _render_create_database():
    """Render the create database section."""
    ui.label("Create Database").classes("text-xl font-bold mb-4")

    # Form fields
    name_input = ui.input("Database name").classes("w-full")

    ui.label("Folders").classes("mt-4 font-medium")
    folders_container = ui.column().classes("w-full gap-2")
    folders_list: list[str] = []

    def refresh_folders():
        """Refresh the folders display."""
        folders_container.clear()
        with folders_container:
            if folders_list:
                for i, folder in enumerate(folders_list):
                    with ui.row().classes("w-full items-center gap-2"):
                        ui.label(folder).classes("flex-1 text-sm truncate")
                        ui.button(
                            icon="close",
                            on_click=lambda idx=i: _remove_folder(idx),
                        ).props("flat dense round size=sm")
            else:
                ui.label("No folders added").classes("text-gray-500 italic text-sm")

    def _remove_folder(index: int):
        folders_list.pop(index)
        refresh_folders()

    def _add_folder():
        folder = api_bridge.select_directory()
        if folder:
            folders_list.append(folder)
            refresh_folders()

    refresh_folders()

    ui.button("Add folder", icon="folder", on_click=_add_folder).props("flat").classes("mt-2")

    # Create button
    def _create_database():
        name = name_input.value.strip()
        if not name:
            ui.notify("Please enter a database name", type="warning")
            return
        if not folders_list:
            ui.notify("Please add at least one folder", type="warning")
            return

        logger.info(f"Creating database: {name} with folders: {folders_list}")
        app_state.database_name = name
        app_state.reset_view()

        result = api_bridge.create_database(name, folders_list, update=True)
        if result.get("error"):
            ui.notify(f"Error: {result['data']['message']}", type="negative")
        else:
            ui.navigate.to("/home")

    ui.button("Create Database", on_click=_create_database).props("color=primary").classes(
        "w-full mt-4"
    )

