# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Pysaurus is a video collection manager (WIP) written in Python 3.13. It handles video metadata extraction, custom properties, advanced search/filtering, video similarity detection, and supports multiple GUI frontends.

## Commands

All commands must be run with `uv run`:

```bash
# Run the application (default GUI: pywebview on Windows, qt on Linux)
uv run -m pysaurus
uv run -m pysaurus pywebview   # or: qtwebview, pyside6

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/unittests/test_example.py

# Run a single test
uv run pytest tests/unittests/test_example.py::test_function_name

# Run tests in parallel
uv run pytest -n auto

# Lint and format
uv run ruff check .
uv run ruff format .
```

## Architecture

### Entry Point

`pysaurus/__main__.py` — selects GUI at runtime based on CLI argument (`pywebview`, `qtwebview`, `pyside6`). Default: pywebview (Windows), qtwebview (Linux).

### Database Layer

Layered separation of concerns:
- **`database/abstract_database.py`** — minimal abstract interface (~20 methods)
- **`database/database_operations.py`** — high-level CRUD operations
- **`database/database_algorithms.py`** — batch processing (update, miniatures, moves)
- **`database/jsdb/json_database.py`** — current implementation using JSON file persistence

### Video Provider

`video_provider/abstract_video_provider.py` — layered filtering/grouping pipeline:
LAYER_SOURCE → LAYER_GROUPING → LAYER_CLASSIFIER → LAYER_GROUP → LAYER_SEARCH → LAYER_SORT

### Properties System

`properties/properties.py` — typed property definitions (bool, int, float, str) with support for multiple values and enumeration.

### GUI Frontends

Multiple implementations in `interface/`:
- `using_pywebview/` — PyWebView (primary on Windows)
- `qtwebview/` — Qt WebView
- `pyside6/` — PySide6

Backend API shared across GUIs: `interface/api/` (feature_api.py, gui_api.py).

### Image Similarity Search

`imgsimsearch/` — uses NumPy for feature extraction and cosine similarity. Annoy was removed because it requires system dependencies (Visual C++ on Windows).

### External Editable Dependencies

- `videre` (at `../videre`) — video extraction
- `skullite` (at `../skullite`) — utility library
- `saurus/sql/` — SQL collection layer (local)

## Code Style

- **Formatter/Linter**: Ruff (`skip-magic-trailing-comma = true`)
- **Python version**: 3.13 (strict: `>=3.13,<3.14`)
- Unused imports allowed in `__init__.py` files (ruff F401 ignored)

## Testing

- pytest with `asyncio_mode = "auto"`
- Test fixtures provide three tiers: `mock_database` (fast in-memory), `mem_*` (temp directory copies), `fake_old_*` / `example_*` (on-disk)
- `pyfakefs` for filesystem mocking, `pytest-qt` for Qt tests, `pytest-xdist` for parallel runs
