# Pysaurus

Video collection manager written in Python 3.13.

Handles video metadata extraction, custom properties, advanced search/filtering,
video similarity detection, and supports multiple GUI frontends.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/) (package manager)
- FFmpeg / ffprobe (for video metadata extraction)

## Usage

All commands must be run with `uv run`:

```bash
# Run the application
uv run -m pysaurus

# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .
```

## GUI Frontends

| Name | Command | Description |
|---|---|---|
| PySide6 | `uv run -m pysaurus pyside6` | Native Qt widgets (primary) |
| PyWebView | `uv run -m pysaurus pywebview` | Web-based (legacy) |
| QtWebView | `uv run -m pysaurus qtwebview` | Qt + web (legacy) |

## Linux Notes

On Linux, the Qt platform plugin may require additional system packages:

```bash
sudo apt install libxcb-cursor-dev
```
