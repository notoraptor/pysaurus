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

# Run CLI (benchmark/debug console, configured via .pysaurus.yaml)
uv run -m pysaurus.interface.console.run --backend sql --db <name>

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

### High-level Flow

```
__main__.py (GUI selector)
    → Interface Layer (PyWebView / PySide6 / QtWebView)
        → GuiAPI / FeatureAPI (proxy-based API)
            → AbstractDatabase
                ├─ .ops → DatabaseOperations (CRUD)
                ├─ .algos → DatabaseAlgorithms (batch processing)
                └─ .provider → AbstractVideoProvider (filtering pipeline)
```

### Entry Point

`pysaurus/__main__.py` — selects GUI at runtime based on CLI argument (`pywebview`, `qtwebview`, `pyside6`). Default: pywebview (Windows), qtwebview (Linux).

### Database Layer

Layered separation of concerns:
- **`database/abstract_database.py`** — minimal abstract interface (~20 methods)
- **`database/database_operations.py`** — high-level CRUD operations (accessed via `db.ops`)
- **`database/database_algorithms.py`** — batch processing: update, miniatures, moves (accessed via `db.algos`)

Two backend implementations, selected by `USE_SQL` flag in `database/database.py` (currently `True`):
- **`database/jsdb/json_database.py`** — legacy JSON file persistence
- **`saurus/sql/pysaurus_collection.py`** — current SQLite implementation (uses `skullite` wrapper)

### SQL Layer (`saurus/sql/`)

- **`pysaurus_collection.py`** — implements `AbstractDatabase` with SQLite
- **`pysaurus_connection.py`** — extends `Skullite` (from `skullite` package), loads schema from `database.sql`
- **`saurus_provider.py`** — implements `AbstractVideoProvider` with SQL queries
- **`video_mega_group.py` / `video_mega_search.py`** — SQL query builders for grouping and search
- **`migration/`** — tools for JSON → SQL migration and verification

### Video Provider

`video_provider/abstract_video_provider.py` — layered filtering/grouping pipeline:
LAYER_SOURCE → LAYER_GROUPING → LAYER_CLASSIFIER → LAYER_GROUP → LAYER_SEARCH → LAYER_SORT

Two implementations: `JsonDatabaseVideoProvider` (Python-based) and `SaurusProvider` (SQL-based).

### API Layer (`interface/api/`)

- **`FeatureAPI`** — base API class exposing 50+ features via proxy pattern. Proxies delegate to `db`, `db.ops`, `db.algos`, `db.provider`, or external tools (clipboard, file dialogs).
- **`GuiAPI`** — extends `FeatureAPI` with Flask video server, thread management, and VLC integration.

All GUI frontends call the same API, ensuring consistent behavior.

### Properties System

`properties/properties.py` — typed property definitions (bool, int, float, str) with support for multiple values and enumeration.

### GUI Frontends

Multiple implementations in `interface/`:
- `using_pywebview/` — PyWebView (primary on Windows)
- `qtwebview/` — Qt WebView
- `pyside6/` — PySide6

### Image Similarity Search

`imgsimsearch/` — uses NumPy for feature extraction and cosine similarity. Annoy was removed because it requires system dependencies (Visual C++ on Windows).

### External Editable Dependencies

- `videre` (at `../videre`) — video extraction
- `skullite` (at `../skullite`) — SQLite wrapper library
- `saurus/sql/` — SQL collection layer (local)

## Code Style

- **Formatter/Linter**: Ruff (`skip-magic-trailing-comma = true`)
- **Python version**: 3.13 (strict: `>=3.13,<3.14`)
- Unused imports allowed in `__init__.py` files (ruff F401 ignored)

## Testing

- pytest with `asyncio_mode = "auto"`
- Test fixtures provide three tiers:
  - **Fast mock**: `mock_database` / `mock_database_readonly` — pure in-memory, no I/O
  - **Writable copies**: `mem_old_database`, `mem_saurus_database`, `example_*_memory` — `shutil.copytree` to `tmp_path`
  - **Read-only on-disk**: `fake_old_database`, `fake_saurus_database`, `example_json_database`, `example_saurus_database`
- `pyfakefs` for filesystem mocking, `pytest-qt` for Qt tests, `pytest-xdist` for parallel runs
