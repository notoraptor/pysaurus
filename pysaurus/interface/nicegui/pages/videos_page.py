"""
Videos Page - Main video browsing interface.
"""

import logging
from typing import Any

from nicegui import ui

from pysaurus.interface.nicegui.api_bridge import api_bridge
from pysaurus.interface.nicegui.components.video_card import video_card
from pysaurus.interface.nicegui.state import app_state
from pysaurus.interface.nicegui.utils.constants import GROUPABLE_FIELDS, SOURCE_TREE

logger = logging.getLogger(__name__)


class ViewMode:
    GRID = "grid"
    LIST = "list"


class VideosPageState:
    """Local state for the videos page."""

    def __init__(self):
        self.videos: list[dict[str, Any]] = []
        self.nb_videos: int = 0
        self.nb_pages: int = 0
        self.page_size: int = 20
        self.page_number: int = 0

        # View mode (grid or list)
        self.view_mode: str = ViewMode.GRID

        # View info
        self.valid_size: str = ""
        self.valid_length: str = ""
        self.nb_view_videos: int = 0
        self.nb_source_videos: int = 0

        # Sources
        self.sources: list[list[str]] = []

        # Grouping
        self.group_def: dict[str, Any] | None = None
        self.classifier_path: list[str] = []

        # Property types for grouping
        self.prop_types: list[dict[str, Any]] = []

        # Search
        self.search_def: dict[str, Any] | None = None

        # Sorting
        self.sorting: list[str] = []

    def load_data(self) -> None:
        """Load videos from backend."""
        try:
            data = api_bridge.backend(self.page_size, self.page_number, None)

            self.videos = data.get("videos", [])
            self.nb_videos = data.get("nbVideos", 0)
            self.nb_pages = data.get("nbPages", 0)
            self.page_size = data.get("pageSize", 20)
            self.page_number = data.get("pageNumber", 0)
            self.valid_size = data.get("validSize", "")
            self.valid_length = data.get("validLength", "")
            self.nb_view_videos = data.get("nbViewVideos", 0)
            self.nb_source_videos = data.get("nbSourceVideos", 0)

            # Load grouping/sources/search info
            self.sources = data.get("sources") or []
            self.group_def = data.get("groupDef")
            self.classifier_path = data.get("path") or []
            self.prop_types = data.get("prop_types") or []
            self.search_def = data.get("searchDef")
            self.sorting = data.get("sorting") or []

            logger.debug(f"Loaded {len(self.videos)} videos (page {self.page_number + 1}/{self.nb_pages})")

        except Exception as e:
            logger.exception("Error loading videos")
            self.videos = []
            ui.notify(f"Error loading videos: {e}", type="negative")

    def toggle_view_mode(self) -> None:
        """Toggle between grid and list view."""
        if self.view_mode == ViewMode.GRID:
            self.view_mode = ViewMode.LIST
        else:
            self.view_mode = ViewMode.GRID


# Global page state
_page_state = VideosPageState()

# Refreshable containers for reactive updates
_video_content_refreshable = None
_stats_bar_refreshable = None
_toolbar_refreshable = None


def videos_page():
    """Render the videos page."""
    global _video_content_refreshable, _stats_bar_refreshable, _toolbar_refreshable

    # Load initial data
    _page_state.load_data()

    with ui.column().classes("w-full h-full"):
        # Toolbar (refreshable for view mode icon update)
        @ui.refreshable
        def toolbar_content():
            _render_toolbar()

        _toolbar_refreshable = toolbar_content
        toolbar_content()

        # Main content area
        with ui.row().classes("w-full flex-1 gap-0"):
            # Left sidebar (collapsible)
            _render_sidebar()

            # Video content area
            with ui.column().classes("flex-1 p-4 overflow-y-auto"):
                # Stats bar (refreshable)
                @ui.refreshable
                def stats_bar_content():
                    _render_stats_bar()

                _stats_bar_refreshable = stats_bar_content
                stats_bar_content()

                # Video content (grid or list) - refreshable
                @ui.refreshable
                def video_content():
                    _render_video_content()

                _video_content_refreshable = video_content
                video_content()

                # Pagination
                _render_pagination()


def _render_toolbar():
    """Render the top toolbar."""
    with ui.row().classes("w-full p-2 bg-gray-100 items-center gap-2"):
        # Refresh button
        ui.button(icon="refresh", on_click=_on_refresh).props("flat").tooltip(
            "Refresh database"
        )

        ui.separator().props("vertical")

        # View mode toggle
        is_grid = _page_state.view_mode == ViewMode.GRID
        ui.button(
            icon="grid_view" if is_grid else "view_list",
            on_click=_on_toggle_view_mode,
        ).props("flat").tooltip(
            "Switch to list view" if is_grid else "Switch to grid view"
        )

        ui.separator().props("vertical")

        # Random video
        ui.button(icon="shuffle", on_click=_on_random_video).props("flat").tooltip(
            "Open random video"
        )

        # Playlist
        ui.button(icon="playlist_play", on_click=_on_playlist).props("flat").tooltip(
            "Create playlist"
        )

        ui.space()

        # Page size selector
        ui.label("Per page:")
        ui.select(
            [10, 20, 50, 100],
            value=_page_state.page_size,
            on_change=_on_page_size_change,
        ).classes("w-20")


def _render_sidebar():
    """Render the left sidebar with filters."""
    with ui.column().classes("w-64 bg-gray-50 p-2 border-r overflow-y-auto"):
        ui.label("Filters").classes("font-bold text-lg mb-2")

        # Sources section
        _render_sources_section()

        # Grouping section
        _render_grouping_section()

        # Search section
        _render_search_section()

        # Sorting section
        with ui.expansion("Sorting", icon="sort").classes("w-full"):
            _render_sorting_section()


def _render_sources_section():
    """Render the sources filter section."""
    # Check if sources are active
    has_sources = bool(_page_state.sources)

    with ui.expansion("Sources", icon="filter_alt", value=has_sources).classes("w-full"):
        if has_sources:
            ui.label(f"{len(_page_state.sources)} filter(s) active").classes("text-sm text-primary mb-2")

            # Show each selected source path
            with ui.column().classes("gap-1 mb-2"):
                for source_path in _page_state.sources:
                    # Format: ["readable", "found"] -> "readable > found"
                    display = " > ".join(s.replace("_", " ") for s in source_path)
                    with ui.row().classes("items-center gap-1"):
                        ui.icon("check", size="xs").classes("text-primary")
                        ui.label(display).classes("text-xs")

            with ui.row().classes("gap-2"):
                ui.button("Edit", on_click=_show_sources_dialog, icon="edit").props("flat dense")
                ui.button("Clear", on_click=_on_clear_sources, icon="clear").props("flat dense")
        else:
            ui.label("Filter by video status").classes("text-sm text-gray-500 mb-2")
            ui.label("(readable, found, thumbnails...)").classes("text-xs text-gray-400 mb-2")

            ui.button("Select sources...", on_click=_show_sources_dialog, icon="filter_alt").props(
                "flat dense"
            ).classes("w-full")


def _render_grouping_section():
    """Render the grouping section."""
    group_def = _page_state.group_def
    is_grouped = group_def and group_def.get("field")

    with ui.expansion("Grouping", icon="workspaces", value=is_grouped).classes("w-full"):
        if is_grouped:
            # Show current grouping info
            field = group_def.get("field", "")
            is_property = group_def.get("is_property", False)
            groups = group_def.get("groups", [])

            with ui.column().classes("w-full gap-1"):
                ui.label(f"Grouped by: {field}").classes("text-sm font-medium")
                ui.label(f"{'Property' if is_property else 'Attribute'}").classes("text-xs text-gray-500")

                if groups:
                    ui.label(f"{len(groups)} groups").classes("text-sm text-primary")

                    # Show classifier path if navigating
                    if _page_state.classifier_path:
                        with ui.row().classes("items-center gap-1"):
                            ui.label("Path:").classes("text-xs")
                            ui.label(" > ".join(_page_state.classifier_path)).classes(
                                "text-xs text-primary truncate"
                            )
                        ui.button("Back", on_click=_on_classifier_back, icon="arrow_back").props(
                            "flat dense"
                        )

                with ui.row().classes("w-full gap-1 mt-2"):
                    ui.button("Clear", on_click=_on_clear_grouping, icon="clear").props("flat dense")
                    ui.button("Edit", on_click=_show_grouping_dialog, icon="edit").props("flat dense")

                # Show groups list
                if groups:
                    ui.separator().classes("my-2")
                    _render_groups_list(groups)
        else:
            ui.label("Group videos by field").classes("text-sm text-gray-500 mb-2")
            ui.button("Set grouping...", on_click=_show_grouping_dialog, icon="workspaces").props(
                "flat dense"
            ).classes("w-full")


def _render_groups_list(groups: list[dict]):
    """Render the list of groups for navigation."""
    with ui.column().classes("w-full gap-1 max-h-48 overflow-y-auto"):
        for group in groups[:20]:  # Limit to first 20 groups
            group_id = group.get("id")
            value = group.get("value", "")
            count = group.get("count", 0)

            # Display value (truncate if too long)
            display_value = str(value) if value else "(empty)"
            if len(display_value) > 20:
                display_value = display_value[:17] + "..."

            with ui.row().classes("w-full items-center hover:bg-gray-100 rounded p-1 cursor-pointer"):
                ui.label(display_value).classes("flex-1 text-sm truncate")
                ui.label(f"({count})").classes("text-xs text-gray-500")

                # Click to select group
                ui.element("div").classes("absolute inset-0").on(
                    "click", lambda gid=group_id: _on_select_group(gid)
                )

        if len(groups) > 20:
            ui.label(f"... and {len(groups) - 20} more").classes("text-xs text-gray-500 italic")


def _render_search_section():
    """Render the search section."""
    search_def = _page_state.search_def
    has_search = search_def and search_def.get("text")

    with ui.expansion("Search", icon="search", value=True).classes("w-full"):
        # Current search info
        if has_search:
            text = search_def.get("text", "")
            cond = search_def.get("cond", "and")
            ui.label(f'"{text}" ({cond})').classes("text-sm text-primary mb-2 truncate")

        search_input = ui.input(
            placeholder="Search videos...",
            value=search_def.get("text", "") if search_def else "",
        ).classes("w-full")
        search_input.on("keydown.enter", lambda: _on_search(search_input.value))

        with ui.row().classes("w-full gap-1 mt-1"):
            ui.button("AND", on_click=lambda: _on_search(search_input.value, "and")).props("flat dense")
            ui.button("OR", on_click=lambda: _on_search(search_input.value, "or")).props("flat dense")
            ui.button("Clear", on_click=_on_clear_search).props("flat dense")


def _render_sorting_section():
    """Render the sorting section."""
    sorting = _page_state.sorting

    if sorting:
        ui.label("Current sorting:").classes("text-sm text-gray-500")
        for field in sorting:
            # Remove "-" prefix for descending
            is_desc = field.startswith("-")
            field_name = field[1:] if is_desc else field
            arrow = "↓" if is_desc else "↑"
            ui.label(f"{arrow} {field_name}").classes("text-sm")

        ui.button("Clear sorting", on_click=_on_clear_sorting, icon="clear").props("flat dense")
    else:
        ui.label("No custom sorting").classes("text-sm text-gray-500")

    ui.button("Set sorting...", on_click=_show_sorting_dialog, icon="sort").props(
        "flat dense"
    ).classes("w-full mt-2")


def _render_stats_bar():
    """Render the statistics bar above the grid."""
    with ui.row().classes("w-full items-center text-sm text-gray-600 mb-2"):
        ui.label(f"{_page_state.nb_videos} videos")
        ui.label("•").classes("mx-2")
        ui.label(f"{_page_state.valid_size}")
        ui.label("•").classes("mx-2")
        ui.label(f"{_page_state.valid_length}")

        ui.space()

        # View mode indicator
        mode_label = "Grid view" if _page_state.view_mode == ViewMode.GRID else "List view"
        ui.label(mode_label).classes("text-primary font-medium")


def _render_video_content():
    """Render video content based on view mode."""
    if _page_state.view_mode == ViewMode.GRID:
        _render_video_grid()
    else:
        _render_video_list()


def _render_video_grid():
    """Render the video grid."""
    grid_container = ui.element("div").classes(
        "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4"
    )

    # Context menu actions for each video (use "---" for separators)
    menu_actions = [
        ("Open", _on_open_video),
        ("Open in VLC", _on_open_in_vlc),
        ("Open folder", _on_open_folder),
        ("---", None),
        ("Mark as watched", _on_mark_watched),
        ("---", None),
        ("Rename", _on_rename),
        ("Delete entry", _on_delete_entry),
        ("Delete file", _on_delete_file),
        ("---", None),
        ("Copy path", _on_copy_path),
    ]

    with grid_container:
        if _page_state.videos:
            for video in _page_state.videos:
                video_card(
                    video,
                    selected=False,
                    on_click=_on_video_click_info,  # Click shows info dialog
                    on_double_click=_on_video_double_click,
                    context_menu_actions=menu_actions,
                )
        else:
            with ui.element("div").classes("col-span-full text-center py-8"):
                ui.label("No videos found").classes("text-gray-500 text-lg")


def _render_video_list():
    """Render the video list."""
    from pysaurus.interface.nicegui.utils.formatters import format_duration, format_resolution

    # Context menu actions
    menu_actions = [
        ("Open", _on_open_video),
        ("Open in VLC", _on_open_in_vlc),
        ("Open folder", _on_open_folder),
        ("---", None),
        ("Mark as watched", _on_mark_watched),
        ("---", None),
        ("Rename", _on_rename),
        ("Delete entry", _on_delete_entry),
        ("Delete file", _on_delete_file),
        ("---", None),
        ("Copy path", _on_copy_path),
    ]

    with ui.column().classes("w-full gap-2"):
        if _page_state.videos:
            for video in _page_state.videos:
                _render_video_list_item(video, menu_actions)
        else:
            with ui.element("div").classes("text-center py-8"):
                ui.label("No videos found").classes("text-gray-500 text-lg")


def _render_video_list_item(video: dict[str, Any], menu_actions: list):
    """Render a single video in list mode with all info."""
    from pysaurus.interface.nicegui.utils.formatters import format_duration, format_resolution, format_file_size

    video_id = video.get("video_id", 0)
    title = video.get("title", "Untitled")
    file_title = video.get("file_title", "")
    thumbnail = video.get("thumbnail_path")
    length = video.get("length", 0)
    width = video.get("width", 0)
    height = video.get("height", 0)
    file_size = video.get("file_size", 0)
    found = video.get("found", True)
    readable = video.get("readable", True)
    watched = video.get("watched", False)
    filename = video.get("filename", "")
    extension = video.get("extension", "")
    frame_rate = video.get("frame_rate", 0)
    bit_rate = video.get("bit_rate") or ""
    video_codec = video.get("video_codec", "")
    audio_codec = video.get("audio_codec", "")
    properties = video.get("properties", {})

    # Row styling based on state
    row_classes = "w-full p-2 border rounded hover:bg-gray-50 cursor-pointer"
    if not found:
        row_classes += " opacity-60 bg-red-50"
    if not readable:
        row_classes += " border-red-500"

    with ui.card().classes(row_classes) as card:
        # Context menu
        with ui.context_menu():
            for label, action in menu_actions:
                if label == "---":
                    ui.separator()
                else:
                    ui.menu_item(label, on_click=lambda a=action: a(video_id))

        # Double-click to open
        card.on("dblclick", lambda: _on_video_double_click(video_id))

        with ui.row().classes("w-full gap-4 items-start"):
            # Thumbnail (small)
            with ui.element("div").classes("w-32 h-20 flex-shrink-0 bg-gray-200 rounded overflow-hidden"):
                if thumbnail:
                    ui.image(thumbnail).classes("w-full h-full object-cover")
                else:
                    with ui.element("div").classes("w-full h-full flex items-center justify-center"):
                        ui.icon("movie", size="lg").classes("text-gray-400")

            # Main info
            with ui.column().classes("flex-1 gap-1 min-w-0"):
                # Title row with status icons
                with ui.row().classes("items-center gap-2"):
                    ui.label(title).classes("font-medium text-lg truncate")
                    if watched:
                        ui.icon("visibility", size="xs").classes("text-green-500").tooltip("Watched")
                    if not found:
                        ui.icon("error", size="xs").classes("text-red-500").tooltip("Not found")
                    if not readable:
                        ui.icon("warning", size="xs").classes("text-orange-500").tooltip("Unreadable")

                # File info row
                with ui.row().classes("text-sm text-gray-600 gap-4 flex-wrap"):
                    ui.label(f"{format_duration(length)}").classes("font-mono")
                    ui.label(f"{format_resolution(width, height)}")
                    ui.label(f"{format_file_size(file_size)}")
                    if frame_rate:
                        ui.label(f"{frame_rate:.1f} fps")
                    if extension:
                        ui.label(f".{extension}").classes("font-mono")

                # Technical info row
                with ui.row().classes("text-xs text-gray-500 gap-4"):
                    if video_codec:
                        ui.label(f"Video: {video_codec}")
                    if audio_codec:
                        ui.label(f"Audio: {audio_codec}")
                    if bit_rate:
                        ui.label(f"{bit_rate}")

                # File path
                ui.label(filename).classes("text-xs text-gray-400 truncate")

            # Properties column
            if properties:
                with ui.column().classes("w-48 flex-shrink-0 gap-1"):
                    ui.label("Properties").classes("text-xs font-medium text-gray-500")
                    for prop_name, prop_value in list(properties.items())[:5]:
                        with ui.row().classes("text-xs gap-1"):
                            ui.label(f"{prop_name}:").classes("text-gray-500")
                            if isinstance(prop_value, list):
                                ui.label(", ".join(str(v) for v in prop_value[:3])).classes("truncate")
                            else:
                                ui.label(str(prop_value)).classes("truncate")
                    if len(properties) > 5:
                        ui.label(f"... +{len(properties) - 5} more").classes("text-xs text-gray-400 italic")


def _render_pagination():
    """Render pagination controls."""
    if _page_state.nb_pages <= 1:
        return

    with ui.row().classes("w-full justify-center items-center gap-2 mt-4"):
        # First page
        ui.button(
            icon="first_page",
            on_click=lambda: _go_to_page(0),
        ).props("flat dense").bind_enabled_from(
            _page_state, "page_number", backward=lambda p: p > 0
        )

        # Previous page
        ui.button(
            icon="chevron_left",
            on_click=lambda: _go_to_page(_page_state.page_number - 1),
        ).props("flat dense").bind_enabled_from(
            _page_state, "page_number", backward=lambda p: p > 0
        )

        # Page indicator
        ui.label(f"Page {_page_state.page_number + 1} / {_page_state.nb_pages}")

        # Next page
        ui.button(
            icon="chevron_right",
            on_click=lambda: _go_to_page(_page_state.page_number + 1),
        ).props("flat dense").bind_enabled_from(
            _page_state, "page_number", backward=lambda p: p < _page_state.nb_pages - 1
        )

        # Last page
        ui.button(
            icon="last_page",
            on_click=lambda: _go_to_page(_page_state.nb_pages - 1),
        ).props("flat dense").bind_enabled_from(
            _page_state, "page_number", backward=lambda p: p < _page_state.nb_pages - 1
        )


# -------------------------------------------------------------------------
# Event handlers
# -------------------------------------------------------------------------


def _on_refresh():
    """Refresh the database."""
    ui.notify("Refreshing database...", type="info")
    api_bridge.update_database()
    ui.navigate.to("/home")


def _on_toggle_view_mode():
    """Toggle between grid and list view."""
    _page_state.toggle_view_mode()
    # Refresh UI components without full page reload
    if _toolbar_refreshable:
        _toolbar_refreshable.refresh()
    if _stats_bar_refreshable:
        _stats_bar_refreshable.refresh()
    if _video_content_refreshable:
        _video_content_refreshable.refresh()


def _on_random_video():
    """Open a random video."""
    result = api_bridge.open_random_video()
    if result.get("error"):
        ui.notify(f"Error: {result['data']['message']}", type="negative")


def _on_playlist():
    """Create and open playlist."""
    try:
        path = api_bridge.playlist()
        ui.notify(f"Playlist created: {path}", type="positive")
    except Exception as e:
        ui.notify(f"Error: {e}", type="negative")


def _on_page_size_change(e):
    """Handle page size change."""
    _page_state.page_size = e.value
    _page_state.page_number = 0
    ui.navigate.to("/videos")


def _go_to_page(page: int):
    """Navigate to a specific page."""
    _page_state.page_number = max(0, min(page, _page_state.nb_pages - 1))
    ui.navigate.to("/videos")


def _on_search(text: str, cond: str = "and"):
    """Execute search."""
    if text:
        api_bridge.set_search(text, cond)
        _page_state.page_number = 0
        ui.navigate.to("/videos")


def _on_clear_search():
    """Clear search."""
    api_bridge.set_search("", "and")
    _page_state.page_number = 0
    ui.navigate.to("/videos")


def _on_video_click_info(video_id: int):
    """Handle video card click - show info dialog."""
    _show_video_info_dialog(video_id)


def _on_video_double_click(video_id: int):
    """Handle video card double-click - open video."""
    api_bridge.open_video(video_id)


def _show_video_info_dialog(video_id: int):
    """Show a dialog with all video information."""
    from pysaurus.interface.nicegui.utils.formatters import format_duration, format_resolution, format_file_size

    # Find video in current list
    video = next((v for v in _page_state.videos if v.get("video_id") == video_id), None)
    if not video:
        ui.notify("Video not found", type="warning")
        return

    title = video.get("title", "Untitled")
    file_title = video.get("file_title", "")
    thumbnail = video.get("thumbnail_path")
    length = video.get("length", 0)
    width = video.get("width", 0)
    height = video.get("height", 0)
    file_size = video.get("file_size", 0)
    found = video.get("found", True)
    readable = video.get("readable", True)
    watched = video.get("watched", False)
    filename = video.get("filename", "")
    extension = video.get("extension", "")
    frame_rate = video.get("frame_rate", 0)
    bit_rate = video.get("bit_rate") or ""
    video_codec = video.get("video_codec", "")
    video_codec_desc = video.get("video_codec_description", "")
    audio_codec = video.get("audio_codec", "")
    audio_codec_desc = video.get("audio_codec_description", "")
    audio_bit_rate = video.get("audio_bit_rate") or ""
    sample_rate = video.get("sample_rate") or 0
    container_format = video.get("container_format", "")
    properties = video.get("properties", {})
    date = video.get("date", "")
    day = video.get("day", "")

    with ui.dialog() as dialog, ui.card().classes("min-w-[600px] max-w-[900px] max-h-[90vh] overflow-y-auto"):
        # Header with title and close button
        with ui.row().classes("w-full items-center mb-4"):
            ui.label(title).classes("text-xl font-bold flex-1 truncate")
            ui.button(icon="close", on_click=dialog.close).props("flat round")

        with ui.row().classes("w-full gap-6"):
            # Left column: thumbnail and actions
            with ui.column().classes("w-64 flex-shrink-0"):
                # Thumbnail
                with ui.element("div").classes("w-full aspect-video bg-gray-200 rounded overflow-hidden mb-4"):
                    if thumbnail:
                        ui.image(thumbnail).classes("w-full h-full object-cover")
                    else:
                        with ui.element("div").classes("w-full h-full flex items-center justify-center"):
                            ui.icon("movie", size="xl").classes("text-gray-400")

                # Status badges
                with ui.row().classes("gap-2 mb-4 flex-wrap"):
                    if watched:
                        ui.badge("Watched", color="green")
                    else:
                        ui.badge("Unwatched", color="gray")
                    if not found:
                        ui.badge("Not Found", color="red")
                    if not readable:
                        ui.badge("Unreadable", color="orange")

                # Action buttons
                with ui.column().classes("w-full gap-2"):
                    ui.button("Open Video", on_click=lambda: [dialog.close(), _on_open_video(video_id)], icon="play_arrow").props("color=primary").classes("w-full")
                    ui.button("Open in VLC", on_click=lambda: [dialog.close(), _on_open_in_vlc(video_id)], icon="smart_display").classes("w-full")
                    ui.button("Open Folder", on_click=lambda: _on_open_folder(video_id), icon="folder_open").props("flat").classes("w-full")
                    ui.button("Toggle Watched", on_click=lambda: [_on_mark_watched(video_id), dialog.close()], icon="visibility").props("flat").classes("w-full")
                    ui.button("Copy Path", on_click=lambda: _on_copy_path(video_id), icon="content_copy").props("flat").classes("w-full")

            # Right column: details
            with ui.column().classes("flex-1 gap-4"):
                # File info section
                with ui.card().classes("w-full").props("flat bordered"):
                    ui.label("File Information").classes("font-bold mb-2")
                    with ui.element("div").classes("grid grid-cols-2 gap-x-4 gap-y-1 text-sm"):
                        ui.label("File name:").classes("text-gray-500")
                        ui.label(file_title or title)

                        ui.label("Extension:").classes("text-gray-500")
                        ui.label(f".{extension}" if extension else "-")

                        ui.label("Size:").classes("text-gray-500")
                        ui.label(format_file_size(file_size))

                        ui.label("Path:").classes("text-gray-500")
                        ui.label(filename).classes("truncate").tooltip(filename)

                        if date:
                            ui.label("Modified:").classes("text-gray-500")
                            ui.label(str(date))

                # Video info section
                with ui.card().classes("w-full").props("flat bordered"):
                    ui.label("Video").classes("font-bold mb-2")
                    with ui.element("div").classes("grid grid-cols-2 gap-x-4 gap-y-1 text-sm"):
                        ui.label("Duration:").classes("text-gray-500")
                        ui.label(format_duration(length))

                        ui.label("Resolution:").classes("text-gray-500")
                        ui.label(format_resolution(width, height))

                        ui.label("Frame rate:").classes("text-gray-500")
                        ui.label(f"{frame_rate:.2f} fps" if frame_rate else "-")

                        ui.label("Bit rate:").classes("text-gray-500")
                        ui.label(str(bit_rate) if bit_rate else "-")

                        ui.label("Codec:").classes("text-gray-500")
                        ui.label(f"{video_codec}" + (f" ({video_codec_desc})" if video_codec_desc else ""))

                        ui.label("Container:").classes("text-gray-500")
                        ui.label(container_format or "-")

                # Audio info section
                with ui.card().classes("w-full").props("flat bordered"):
                    ui.label("Audio").classes("font-bold mb-2")
                    with ui.element("div").classes("grid grid-cols-2 gap-x-4 gap-y-1 text-sm"):
                        ui.label("Codec:").classes("text-gray-500")
                        ui.label(f"{audio_codec}" + (f" ({audio_codec_desc})" if audio_codec_desc else "") if audio_codec else "-")

                        ui.label("Bit rate:").classes("text-gray-500")
                        ui.label(str(audio_bit_rate) if audio_bit_rate else "-")

                        ui.label("Sample rate:").classes("text-gray-500")
                        ui.label(f"{sample_rate} Hz" if sample_rate else "-")

                # Properties section
                if properties:
                    with ui.card().classes("w-full").props("flat bordered"):
                        ui.label("Properties").classes("font-bold mb-2")
                        with ui.element("div").classes("grid grid-cols-2 gap-x-4 gap-y-1 text-sm"):
                            for prop_name, prop_value in properties.items():
                                ui.label(f"{prop_name}:").classes("text-gray-500")
                                if isinstance(prop_value, list):
                                    ui.label(", ".join(str(v) for v in prop_value))
                                else:
                                    ui.label(str(prop_value))

    dialog.open()


# -------------------------------------------------------------------------
# Context menu actions (all receive video_id directly)
# -------------------------------------------------------------------------


def _on_open_video(video_id: int):
    """Open the video."""
    api_bridge.open_video(video_id)


def _on_open_in_vlc(video_id: int):
    """Open video in VLC from server."""
    result = api_bridge.open_from_server(video_id)
    if result.get("error"):
        ui.notify(f"Error: {result['data']['message']}", type="negative")


def _on_open_folder(video_id: int):
    """Open containing folder."""
    api_bridge.open_containing_folder(video_id)


def _on_mark_watched(video_id: int):
    """Toggle watched status."""
    api_bridge.mark_as_read(video_id)
    ui.navigate.to("/videos")


def _on_rename(video_id: int):
    """Show rename dialog."""
    # Find video
    video = next(
        (v for v in _page_state.videos if v["video_id"] == video_id),
        None,
    )
    if not video:
        return

    with ui.dialog() as dialog, ui.card():
        ui.label("Rename video").classes("text-lg font-bold")
        name_input = ui.input("New name", value=video.get("file_title", "")).classes(
            "w-full min-w-[300px]"
        )

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Rename",
                on_click=lambda: _do_rename(dialog, video_id, name_input.value),
            ).props("color=primary")

    dialog.open()


def _do_rename(dialog, video_id: int, new_name: str):
    """Execute rename."""
    if new_name:
        result = api_bridge.rename_video(video_id, new_name)
        if result.get("error"):
            ui.notify(f"Error: {result['data']['message']}", type="negative")
        else:
            ui.notify("Video renamed", type="positive")
            dialog.close()
            ui.navigate.to("/videos")


def _on_delete_entry(video_id: int):
    """Delete video entry (keep file)."""
    with ui.dialog() as dialog, ui.card():
        ui.label("Delete entry?").classes("text-lg font-bold")
        ui.label("The video file will be kept on disk.").classes("text-gray-600")

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Delete",
                on_click=lambda: _do_delete_entry(dialog, video_id),
            ).props("color=negative")

    dialog.open()


def _do_delete_entry(dialog, video_id: int):
    """Execute delete entry."""
    result = api_bridge.call("delete_video_entry", video_id)
    if result.get("error"):
        ui.notify(f"Error: {result['data']['message']}", type="negative")
    else:
        ui.notify("Entry deleted", type="positive")
        dialog.close()
        ui.navigate.to("/videos")


def _on_delete_file(video_id: int):
    """Delete video file and entry."""
    with ui.dialog() as dialog, ui.card():
        ui.label("Delete video file?").classes("text-lg font-bold text-red-600")
        ui.label("This will permanently delete the file from disk!").classes(
            "text-red-500"
        )

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Delete permanently",
                on_click=lambda: _do_delete_file(dialog, video_id),
            ).props("color=negative")

    dialog.open()


def _do_delete_file(dialog, video_id: int):
    """Execute delete file."""
    result = api_bridge.delete_video(video_id)
    if result.get("error"):
        ui.notify(f"Error: {result['data']['message']}", type="negative")
    else:
        ui.notify("Video deleted", type="positive")
        dialog.close()
        ui.navigate.to("/videos")


def _on_copy_path(video_id: int):
    """Copy video path to clipboard."""
    video = next(
        (v for v in _page_state.videos if v["video_id"] == video_id),
        None,
    )
    if video:
        path = video.get("filename", "")
        api_bridge.clipboard(path)
        ui.notify("Path copied to clipboard", type="positive")


# -------------------------------------------------------------------------
# Sources handling
# -------------------------------------------------------------------------


def _get_subtree(tree: dict, entry_name: str) -> dict | None:
    """Get a subtree from the source tree by path."""
    steps = entry_name.split("-")
    subtree = tree
    for step in steps:
        if subtree is None:
            return None
        subtree = subtree.get(step)
    return subtree


def _collect_all_paths(tree: dict | None, prefix: str = "") -> list[str]:
    """Collect all possible paths from a tree (including the prefix itself if it has children)."""
    paths = []
    if tree is not None:
        if prefix:
            paths.append(prefix)
        for name, subtree in tree.items():
            entry_name = f"{prefix}-{name}" if prefix else name
            paths.extend(_collect_all_paths(subtree, entry_name))
    else:
        if prefix:
            paths.append(prefix)
    return paths


def _add_paths(old_paths: list[str], new_paths: list[str]) -> list[str]:
    """Add paths to list without duplicates."""
    result = old_paths.copy()
    for path in new_paths:
        if path not in result:
            result.append(path)
    result.sort()
    return result


def _remove_paths(old_paths: list[str], paths_to_remove: list[str]) -> list[str]:
    """Remove paths from list."""
    return [p for p in old_paths if p not in paths_to_remove]


def _show_sources_dialog():
    """Show the sources selection dialog with select/develop pattern."""
    # Build current paths as strings
    initial_paths = ["-".join(path) for path in _page_state.sources]

    # Use a mutable container for state
    state = {"paths": initial_paths.copy()}

    def has_path(path: str) -> bool:
        return path in state["paths"]

    with ui.dialog() as dialog, ui.card().classes("min-w-[500px] max-h-[80vh]"):
        ui.label("Select Video Sources").classes("text-xl font-bold mb-4")

        ui.label("Filter videos by their status (readable, found, thumbnails).").classes(
            "text-sm text-gray-600 mb-4"
        )

        # Tree container (refreshable)
        tree_container = ui.column().classes("w-full")

        # Selected paths display (refreshable)
        selected_container = ui.column().classes("w-full mt-4 pt-4 border-t")

        def refresh_ui():
            """Refresh both tree and selected paths display."""
            render_tree()
            render_selected()

        def render_tree():
            """Render the source tree with select/develop pattern."""
            tree_container.clear()
            with tree_container:
                _render_source_tree(SOURCE_TREE, "", state, refresh_ui)

        def render_selected():
            """Render the list of selected paths."""
            selected_container.clear()
            with selected_container:
                ui.label("Currently selected:").classes("font-medium text-sm")
                if state["paths"]:
                    with ui.column().classes("mt-2 gap-1"):
                        for path in sorted(state["paths"]):
                            # Format path nicely: "readable-found-with_thumbnails" -> "readable > found > with_thumbnails"
                            display = path.replace("-", " > ").replace("_", " ")
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("check_circle", size="xs").classes("text-primary")
                                ui.label(display).classes("text-sm")
                else:
                    ui.label("None selected (will show all readable videos)").classes(
                        "text-sm text-gray-500 italic mt-2"
                    )

        # Initial render
        render_tree()
        render_selected()

        # Buttons
        with ui.row().classes("w-full justify-end gap-2 mt-4 pt-4 border-t"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Apply",
                on_click=lambda: _apply_sources(dialog, state["paths"]),
            ).props("color=primary")

    dialog.open()


def _render_source_tree(tree: dict, prefix: str, state: dict, refresh_callback):
    """Recursively render the source tree with select/develop radio buttons."""
    with ui.element("ul").classes("list-none pl-4"):
        for name, subtree in tree.items():
            entry_name = f"{prefix}-{name}" if prefix else name
            is_selected = entry_name in state["paths"]
            display_name = name.replace("_", " ")

            with ui.element("li").classes("my-2"):
                if subtree is not None:
                    # Branch node - use radio buttons (select vs develop)
                    with ui.column().classes("gap-1"):
                        ui.label(display_name).classes("font-medium text-base")

                        with ui.row().classes("items-center gap-4 ml-2"):
                            # Radio group using toggle
                            with ui.row().classes("items-center gap-1"):
                                radio_select = ui.radio(
                                    options={"select": "select", "develop": "develop"},
                                    value="select" if is_selected else "develop",
                                ).props("dense inline")

                                def on_radio_change(e, en=entry_name, st=subtree):
                                    if e.value == "select":
                                        # Remove all child paths and add this path
                                        paths_to_remove = _collect_all_paths(st, en)
                                        state["paths"] = _remove_paths(state["paths"], paths_to_remove)
                                        state["paths"] = _add_paths(state["paths"], [en])
                                    else:  # develop
                                        # Just remove this path (allow children to be selected)
                                        state["paths"] = _remove_paths(state["paths"], [en])
                                    refresh_callback()

                                radio_select.on("update:model-value", on_radio_change)

                        # Show children only if "develop" is selected (not this branch)
                        if not is_selected:
                            _render_source_tree(subtree, entry_name, state, refresh_callback)

                else:
                    # Leaf node - use checkbox
                    with ui.row().classes("items-center gap-2"):
                        cb = ui.checkbox(display_name, value=is_selected).classes("font-medium")

                        def on_checkbox_change(e, en=entry_name):
                            if e.value:
                                state["paths"] = _add_paths(state["paths"], [en])
                            else:
                                state["paths"] = _remove_paths(state["paths"], [en])
                            refresh_callback()

                        cb.on("update:model-value", on_checkbox_change)


def _apply_sources(dialog, paths: list[str]):
    """Apply the selected sources."""
    # Convert paths back to list of lists
    source_paths = [path.split("-") for path in paths] if paths else []
    api_bridge.set_sources(source_paths)
    dialog.close()
    _page_state.page_number = 0
    ui.navigate.to("/videos")


def _on_clear_sources():
    """Clear source filters."""
    api_bridge.set_sources([])
    _page_state.page_number = 0
    ui.navigate.to("/videos")


# -------------------------------------------------------------------------
# Grouping handling
# -------------------------------------------------------------------------


def _show_grouping_dialog():
    """Show the grouping configuration dialog."""
    group_def = _page_state.group_def or {}

    with ui.dialog() as dialog, ui.card().classes("min-w-[400px]"):
        ui.label("Group Videos").classes("text-lg font-bold mb-4")

        # Field type selection
        is_property = ui.checkbox(
            "Group by property (vs attribute)",
            value=group_def.get("is_property", False),
        )

        # Field selection (depends on is_property)
        field_container = ui.column().classes("w-full")

        def update_field_options():
            field_container.clear()
            with field_container:
                if is_property.value:
                    # Property fields
                    if _page_state.prop_types:
                        options = {pt["name"]: pt["name"] for pt in _page_state.prop_types}
                        current = group_def.get("field", _page_state.prop_types[0]["name"]) if group_def.get("is_property") else _page_state.prop_types[0]["name"]
                    else:
                        options = {}
                        current = None
                        ui.label("No properties defined").classes("text-gray-500 italic")
                else:
                    # Attribute fields
                    options = {name: title for name, title, _ in GROUPABLE_FIELDS}
                    current = group_def.get("field", GROUPABLE_FIELDS[0][0]) if not group_def.get("is_property") else GROUPABLE_FIELDS[0][0]

                if options:
                    return ui.select(
                        options,
                        value=current,
                        label="Field",
                    ).classes("w-full")
            return None

        field_select = update_field_options()
        is_property.on("change", lambda: update_field_options())

        # Sorting
        sorting_select = ui.select(
            {"field": "Field value", "length": "Value length", "count": "Group size"},
            value=group_def.get("sorting", "field"),
            label="Sort groups by",
        ).classes("w-full")

        # Reverse
        reverse_cb = ui.checkbox("Reverse order", value=group_def.get("reverse", False))

        # Allow singletons
        singletons_cb = ui.checkbox(
            "Allow singletons (groups with 1 video)",
            value=group_def.get("allow_singletons", True),
        )

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Apply",
                on_click=lambda: _apply_grouping(
                    dialog,
                    field_select.value if field_select else None,
                    is_property.value,
                    sorting_select.value,
                    reverse_cb.value,
                    singletons_cb.value,
                ),
            ).props("color=primary")

    dialog.open()


def _apply_grouping(dialog, field: str | None, is_property: bool, sorting: str, reverse: bool, allow_singletons: bool):
    """Apply the grouping configuration."""
    if not field:
        ui.notify("Please select a field", type="warning")
        return

    result = api_bridge.set_groups(field, is_property, sorting, reverse, allow_singletons)
    if result.get("error"):
        ui.notify(f"Error: {result['data']['message']}", type="negative")
    else:
        dialog.close()
        _page_state.page_number = 0
        ui.navigate.to("/videos")


def _on_clear_grouping():
    """Clear grouping."""
    # Set grouping to None by setting an empty field
    api_bridge.set_groups("", False, "field", False, True)
    _page_state.page_number = 0
    ui.navigate.to("/videos")


def _on_select_group(group_id):
    """Select a group in the classifier."""
    result = api_bridge.classifier_select_group(group_id)
    if result.get("error"):
        ui.notify(f"Error: {result['data']['message']}", type="negative")
    else:
        _page_state.page_number = 0
        ui.navigate.to("/videos")


def _on_classifier_back():
    """Go back in the classifier path."""
    result = api_bridge.classifier_back()
    if result.get("error"):
        ui.notify(f"Error: {result['data']['message']}", type="negative")
    else:
        _page_state.page_number = 0
        ui.navigate.to("/videos")


# -------------------------------------------------------------------------
# Sorting handling
# -------------------------------------------------------------------------


def _show_sorting_dialog():
    """Show the sorting configuration dialog."""
    current_sorting = _page_state.sorting.copy()

    with ui.dialog() as dialog, ui.card().classes("min-w-[400px]"):
        ui.label("Sort Videos").classes("text-lg font-bold mb-4")

        # Sorting fields list
        sorting_list: list[str] = current_sorting.copy()

        sort_container = ui.column().classes("w-full")

        def refresh_sort_list():
            sort_container.clear()
            with sort_container:
                if sorting_list:
                    for i, field in enumerate(sorting_list):
                        is_desc = field.startswith("-")
                        field_name = field[1:] if is_desc else field

                        with ui.row().classes("w-full items-center gap-2"):
                            ui.label(f"{i + 1}.").classes("text-sm w-6")

                            # Field name
                            ui.label(field_name).classes("flex-1")

                            # Direction toggle
                            ui.button(
                                icon="arrow_downward" if is_desc else "arrow_upward",
                                on_click=lambda idx=i: _toggle_sort_direction(sorting_list, idx, refresh_sort_list),
                            ).props("flat dense round")

                            # Remove
                            ui.button(
                                icon="close",
                                on_click=lambda idx=i: _remove_sort_field(sorting_list, idx, refresh_sort_list),
                            ).props("flat dense round color=negative")
                else:
                    ui.label("No sorting configured").classes("text-gray-500 italic")

        refresh_sort_list()

        # Add new field
        ui.separator().classes("my-2")
        ui.label("Add sorting field:").classes("text-sm font-medium")

        field_options = {name: title for name, title, _ in GROUPABLE_FIELDS}
        new_field_select = ui.select(field_options, label="Field").classes("w-full")

        with ui.row().classes("w-full gap-2"):
            ui.button(
                "Add ascending",
                on_click=lambda: _add_sort_field(sorting_list, new_field_select.value, False, refresh_sort_list),
                icon="arrow_upward",
            ).props("flat dense")
            ui.button(
                "Add descending",
                on_click=lambda: _add_sort_field(sorting_list, new_field_select.value, True, refresh_sort_list),
                icon="arrow_downward",
            ).props("flat dense")

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Apply",
                on_click=lambda: _apply_sorting(dialog, sorting_list),
            ).props("color=primary")

    dialog.open()


def _toggle_sort_direction(sorting_list: list[str], index: int, refresh_callback):
    """Toggle sort direction for a field."""
    field = sorting_list[index]
    if field.startswith("-"):
        sorting_list[index] = field[1:]
    else:
        sorting_list[index] = f"-{field}"
    refresh_callback()


def _remove_sort_field(sorting_list: list[str], index: int, refresh_callback):
    """Remove a sort field."""
    sorting_list.pop(index)
    refresh_callback()


def _add_sort_field(sorting_list: list[str], field: str | None, descending: bool, refresh_callback):
    """Add a new sort field."""
    if not field:
        ui.notify("Please select a field", type="warning")
        return

    sort_field = f"-{field}" if descending else field

    # Check if already in list
    for existing in sorting_list:
        existing_name = existing[1:] if existing.startswith("-") else existing
        if existing_name == field:
            ui.notify("Field already in sorting list", type="warning")
            return

    sorting_list.append(sort_field)
    refresh_callback()


def _apply_sorting(dialog, sorting_list: list[str]):
    """Apply the sorting configuration."""
    result = api_bridge.set_sorting(sorting_list)
    if result.get("error"):
        ui.notify(f"Error: {result['data']['message']}", type="negative")
    else:
        dialog.close()
        _page_state.page_number = 0
        ui.navigate.to("/videos")


def _on_clear_sorting():
    """Clear sorting."""
    api_bridge.set_sorting([])
    _page_state.page_number = 0
    ui.navigate.to("/videos")