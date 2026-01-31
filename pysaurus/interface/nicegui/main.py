"""
Main entry point for NiceGUI interface.
"""

import logging

from nicegui import app, ui

from pysaurus.core.informer import Information
from pysaurus.interface.nicegui.api_bridge import api_bridge
from pysaurus.interface.nicegui.pages.databases_page import databases_page
from pysaurus.interface.nicegui.pages.home_page import home_page
from pysaurus.interface.nicegui.pages.properties_page import properties_page
from pysaurus.interface.nicegui.pages.videos_page import videos_page
from pysaurus.interface.nicegui.state import Page, app_state

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_header():
    """Create the application header with navigation."""
    with ui.header().classes("bg-primary text-white"):
        ui.label("Pysaurus").classes("text-xl font-bold")
        ui.space()

        # Navigation buttons (only show when database is open)
        if app_state.database_name:
            with ui.row():
                ui.button("Videos", on_click=lambda: ui.navigate.to("/videos")).props(
                    "flat color=white"
                )
                ui.button(
                    "Properties", on_click=lambda: ui.navigate.to("/properties")
                ).props("flat color=white")
                ui.button("Databases", on_click=lambda: ui.navigate.to("/")).props(
                    "flat color=white"
                )

            ui.space()
            ui.label(f"DB: {app_state.database_name}").classes("text-sm")


def create_footer():
    """Create the application footer."""
    with ui.footer().classes("bg-gray-100"):
        ui.label("Pysaurus - Video Collection Manager").classes("text-xs text-gray-500")


@ui.page("/")
def index_page():
    """Root page - Database selection."""
    app_state.current_page = Page.DATABASES
    create_header()
    databases_page()
    create_footer()


@ui.page("/home")
def progress_page():
    """Progress/Home page - Shows loading progress."""
    app_state.current_page = Page.HOME
    create_header()
    home_page()
    create_footer()


@ui.page("/videos")
def videos_page_route():
    """Videos page - Main video browsing interface."""
    app_state.current_page = Page.VIDEOS
    create_header()
    videos_page()
    create_footer()


@ui.page("/properties")
def properties_page_route():
    """Properties page - Manage video properties."""
    app_state.current_page = Page.PROPERTIES
    create_header()
    properties_page()
    create_footer()


def on_shutdown():
    """Cleanup on application shutdown."""
    logger.info("Shutting down...")
    api_bridge.close_app()


def main(native: bool = True):
    """Main entry point.

    Args:
        native: If True, run in native desktop window (requires pywebview).
                If False, run in browser.
    """
    with Information():
        logger.info(f"Starting Pysaurus NiceGUI interface (native={native})...")

        # Register shutdown handler
        app.on_shutdown(on_shutdown)

        # Run the NiceGUI app
        ui.run(
            title="Pysaurus",
            port=8080,
            reload=False,
            show=True,
            native=native,
            window_size=(1400, 900),
            frameless=False,
        )


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    # Default is native (pywebview), use --browser to open in browser instead
    browser_mode = "--browser" in sys.argv or "-b" in sys.argv
    main(native=not browser_mode)
