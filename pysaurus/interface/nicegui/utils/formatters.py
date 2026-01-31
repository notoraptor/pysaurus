"""
Formatting utilities for display.
"""

from pysaurus.core.file_size import FileSize


def format_duration(length_str: str) -> str:
    """Format duration string for display.

    Input is already formatted like "1:23:45" or "0:05:30".
    Just return as-is or simplify if needed.
    """
    return length_str or "—"


def format_size(size_str: str) -> str:
    """Format file size string for display.

    Input is already formatted like "1.5 GB" or "500 MB".
    """
    return size_str or "—"


def format_resolution(width: int, height: int) -> str:
    """Format video resolution."""
    if not width or not height:
        return "—"
    return f"{width}x{height}"


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable format."""
    if not size_bytes:
        return "—"
    return str(FileSize(size_bytes))


def truncate(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."