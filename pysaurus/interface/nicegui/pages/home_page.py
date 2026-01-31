"""
Home Page - Progress and notifications display.
"""

import logging
from typing import Any

from nicegui import ui

from pysaurus.interface.nicegui.api_bridge import api_bridge
from pysaurus.interface.nicegui.state import app_state

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Track progress of background jobs."""

    def __init__(self):
        self.jobs: dict[str, dict[str, Any]] = {}
        self.messages: list[str] = []
        self.is_ready = False

    def handle_notification(self, notification: dict[str, Any]) -> None:
        """Process a notification from the backend."""
        name = notification.get("name", "")
        data = notification.get("notification", {})
        message = notification.get("message", "")

        logger.debug(f"Notification: {name} - {message}")

        if name == "JobToDo":
            # New job started
            job_name = data.get("name", "unknown")
            self.jobs[job_name] = {
                "title": data.get("title", job_name),
                "total": data.get("total", 0),
                "current": 0,
                "channels": {},
            }

        elif name == "JobStep":
            # Job progress
            job_name = data.get("name", "unknown")
            if job_name in self.jobs:
                job = self.jobs[job_name]
                channel = data.get("channel")
                step = data.get("step", 0)
                job["channels"][channel] = step
                job["current"] = sum(job["channels"].values())
                # Remove completed jobs
                if job["current"] >= job["total"]:
                    del self.jobs[job_name]

        elif name == "DatabaseReady":
            self.is_ready = True
            self.messages.append("Database ready!")

        elif name == "Done":
            self.messages.append("Done!")

        elif name == "Cancelled":
            self.messages.append("Cancelled.")

        elif name == "End":
            self.messages.append(message or "End.")

        elif name == "ProfilingEnd":
            if message:
                self.messages.append(message)

        elif name in ("ProfilingStart",):
            # Ignore these
            pass

        else:
            # Other notifications
            if message:
                self.messages.append(message)

        # Keep only last 50 messages
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]


# Global progress tracker
progress_tracker = ProgressTracker()


def home_page():
    """Render the home/progress page."""

    # Register notification handler
    def on_notification(notification: dict[str, Any]):
        progress_tracker.handle_notification(notification)
        # Trigger UI update
        ui.update()

    api_bridge.add_notification_handler(on_notification)

    with ui.column().classes("w-full max-w-2xl mx-auto p-4 gap-4"):
        # Title
        ui.label("Loading Database").classes("text-2xl font-bold text-center")

        if app_state.database_name:
            ui.label(app_state.database_name).classes("text-xl text-gray-500 text-center")

        # Progress section
        progress_card = ui.card().classes("w-full")

        # Messages section
        messages_card = ui.card().classes("w-full")

        # Cancel button
        with ui.row().classes("w-full justify-center gap-4"):
            ui.button("Cancel", on_click=_on_cancel).props("color=negative")

        # Timer to refresh UI
        def refresh_ui():
            _refresh_progress(progress_card)
            _refresh_messages(messages_card)

            # Auto-navigate when ready
            if progress_tracker.is_ready:
                progress_tracker.is_ready = False
                api_bridge.remove_notification_handler(on_notification)
                ui.navigate.to("/videos")

        ui.timer(0.1, refresh_ui)

        # Initial render
        refresh_ui()


def _refresh_progress(container: ui.card):
    """Refresh the progress display."""
    container.clear()

    with container:
        if progress_tracker.jobs:
            for job_name, job in progress_tracker.jobs.items():
                with ui.column().classes("w-full gap-1"):
                    ui.label(job["title"]).classes("font-medium")

                    total = job["total"]
                    current = job["current"]
                    percentage = (current / total * 100) if total > 0 else 0

                    ui.linear_progress(value=percentage / 100).classes("w-full")

                    ui.label(f"{current} / {total} ({percentage:.1f}%)").classes(
                        "text-sm text-gray-500"
                    )
        else:
            with ui.row().classes("w-full justify-center items-center gap-2"):
                ui.spinner(size="lg")
                ui.label("Loading...").classes("text-gray-500")


def _refresh_messages(container: ui.card):
    """Refresh the messages display."""
    container.clear()

    with container:
        ui.label("Activity Log").classes("font-bold mb-2")

        if progress_tracker.messages:
            # Show last 10 messages
            with ui.scroll_area().classes("w-full h-48"):
                for message in progress_tracker.messages[-10:]:
                    ui.label(message).classes("text-sm text-gray-600")
        else:
            ui.label("No messages yet...").classes("text-sm text-gray-400 italic")


def _on_cancel():
    """Handle cancel button click."""
    logger.info("Cancelling...")
    api_bridge.cancel_copy()
    ui.notify("Cancel requested", type="info")