"""
Video Card Component - Displays a single video with thumbnail.
"""

from typing import Any, Callable

from nicegui import ui

from pysaurus.interface.nicegui.utils.formatters import format_duration, format_resolution


# Type alias for context menu actions (list of tuples: label, callback)
ContextMenuActions = list[tuple[str, Callable[[int], None] | None]]


def video_card(
    video: dict[str, Any],
    selected: bool = False,
    on_click: Callable[[int], None] | None = None,
    on_double_click: Callable[[int], None] | None = None,
    context_menu_actions: ContextMenuActions | None = None,
):
    """
    Render a video card with thumbnail and info.

    Args:
        video: Video data dictionary from backend
        selected: Whether the video is selected
        on_click: Callback when card is clicked (receives video_id)
        on_double_click: Callback when card is double-clicked (receives video_id)
        context_menu_actions: Dict of menu item labels to callbacks (receives video_id)
    """
    video_id = video.get("video_id", 0)
    title = video.get("title", "Untitled")
    thumbnail = video.get("thumbnail_path")
    length = video.get("length", "")
    width = video.get("width", 0)
    height = video.get("height", 0)
    found = video.get("found", True)
    readable = video.get("readable", True)
    watched = video.get("watched", False)

    # Card styling based on state
    card_classes = "cursor-pointer transition-all duration-200 hover:shadow-lg overflow-hidden"
    if selected:
        card_classes += " ring-2 ring-primary"
    if not found:
        card_classes += " opacity-60"
    if not readable:
        card_classes += " border-red-500 border-2"

    with ui.card().classes(card_classes) as card:
        # Set up click handlers
        if on_click:
            card.on("click", lambda: on_click(video_id))
        if on_double_click:
            card.on("dblclick", lambda: on_double_click(video_id))

        # Context menu (attached to card, appears at mouse position)
        if context_menu_actions:
            with ui.context_menu():
                for label, action in context_menu_actions:
                    if label == "---":
                        ui.separator()
                    else:
                        ui.menu_item(label, on_click=lambda a=action: a(video_id))

        # Thumbnail
        with ui.element("div").classes("relative w-full aspect-video bg-gray-200"):
            if thumbnail:
                ui.image(thumbnail).classes("w-full h-full object-cover")
            else:
                # Placeholder for missing thumbnail
                with ui.element("div").classes(
                    "w-full h-full flex items-center justify-center text-gray-400"
                ):
                    ui.icon("movie", size="xl")

            # Duration badge (bottom-right)
            if length:
                with ui.element("div").classes(
                    "absolute bottom-1 right-1 bg-black/75 text-white text-xs px-1 rounded"
                ):
                    ui.label(format_duration(length))

            # Status indicators (top-left)
            with ui.element("div").classes("absolute top-1 left-1 flex gap-1"):
                if watched:
                    ui.icon("visibility", size="xs").classes(
                        "bg-green-500 text-white rounded p-0.5"
                    ).tooltip("Watched")
                if not found:
                    ui.icon("error", size="xs").classes(
                        "bg-red-500 text-white rounded p-0.5"
                    ).tooltip("File not found")
                if not readable:
                    ui.icon("warning", size="xs").classes(
                        "bg-orange-500 text-white rounded p-0.5"
                    ).tooltip("Unreadable")

        # Video info
        with ui.element("div").classes("p-2 w-full overflow-hidden"):
            # Title (truncated) - must have max-width to truncate properly
            ui.label(title).classes(
                "font-medium text-sm truncate block w-full"
            ).tooltip(title)

            # Resolution
            with ui.row().classes("text-xs text-gray-500 gap-2"):
                ui.label(format_resolution(width, height))

    return card