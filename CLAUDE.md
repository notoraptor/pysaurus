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

### Web Frontend (React/Babel)

The web frontend lives in `pysaurus/interface/web/`. It uses React 18 + Babel + SystemJS (no bundler like Webpack/Vite).

```bash
# Watch and auto-compile JSX (from pysaurus/interface/web/)
npx babel --watch src --out-dir build --presets @babel/preset-react --plugins @babel/plugin-transform-modules-systemjs

# Format frontend code
npm run format
```

Edit files in `src/` — the `build/` directory is auto-generated.

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

### Two Top-level Python Packages

- **`pysaurus/`** — core application code
- **`saurus/`** — SQL-specific layer (separate top-level package, not inside `pysaurus/`)

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

Key schema notes (`saurus/sql/database.sql`):
- `video` table uses **virtual generated columns** (e.g., `readable`, `found`, `length_seconds`, `bit_rate`, `day`, `year`)
- `video_text` is an **FTS5 virtual table** for full-text search with triggers to stay in sync
- Property value triggers are managed manually in Python (not SQL triggers) for batch performance

### Video Provider

`video_provider/abstract_video_provider.py` — layered filtering/grouping pipeline:
LAYER_SOURCE → LAYER_GROUPING → LAYER_CLASSIFIER → LAYER_GROUP → LAYER_SEARCH → LAYER_SORT

Two implementations: `JsonDatabaseVideoProvider` (Python-based) and `SaurusProvider` (SQL-based).

### API Layer — Proxy Pattern (`interface/api/`)

All frontends call `api.__run_feature__(name, *args)`, which looks up a proxy dict, then falls back to calling `self.<name>(*args)` directly.

**`ProxyFeature`** (`api_utils/proxy_feature.py`) wraps `(getter_fn, method, returns_value)`:
1. Calls `getter()` to get the live target (db, provider, etc.)
2. Calls `getattr(target, method.__name__)(*args)`
3. Returns the result only if `returns=True`; otherwise returns `None` (side-effect only)

Proxy subclasses and their targets:

| Class | Target | Use case |
|---|---|---|
| `FromDb` | `api.database` | Direct `AbstractDatabase` methods |
| `FromView` | `api.database.provider` | `AbstractVideoProvider` methods |
| `FromApp` | `api.application` | `Application` methods |
| `FromOps` | `DatabaseOperations(api.database)` | CRUD via `db.ops` |
| `FromAlgo` | `DatabaseAlgorithms(api.database)` | Batch processing via `db.algos` |
| `FromTk` | `filedial` module | File dialog calls |
| `FromPyperclip` | `pyperclip` module | Clipboard operations |

- **`FeatureAPI`** — base API class exposing 50+ features via these proxies.
- **`GuiAPI`** — extends `FeatureAPI` with Flask video server (`ServerLauncher`), thread management, VLC integration, and an abstract `_notify()` method each frontend implements.

### Notification System

Python backend sends typed `Notification` objects (`pysaurus/core/notifications.py`) — e.g., `DatabaseReady`, `Done`, `JobToDo`, `JobStep`. These are serialized to dicts and forwarded to the frontend via `window.NOTIFICATION_MANAGER.call(notification)`.

### GUI Frontends

| Name | Module | Mechanism | Default on |
|---|---|---|---|
| `pywebview` | `using_pywebview/` | Flask HTTP server + `webview` JS bridge | Windows |
| `qtwebview` | `qtwebview/` | `PySide6.QtWebEngineWidgets` + `QWebChannel` | Linux |
| `pyside6` | `pyside6/` | Native Qt widgets (no web) | — |

### Web Frontend (`interface/web/`)

- **Stack**: React 18, SystemJS, Babel (JSX transpilation), PropTypes
- **`BaseComponent`** (`src/BaseComponent.js`): base React component that auto-binds all methods and adds `setStateAsync()`
- **`Backend`** static class (`src/utils/backend.js`): all Python API calls go through `python_call(name, ...args)` → `window.backend_call(name, args)`. `backend_call` is injected by the runtime (CEF = `window.python.call`, Qt = QWebChannel `backend.call`)
- **Pages**: `DatabasesPage`, `HomePage`, `VideosPage`, `PropertiesPage`

### Properties System

`properties/properties.py` — typed property definitions (bool, int, float, str) with support for multiple values and enumeration.

### Image Similarity Search

`imgsimsearch/` — uses NumPy for feature extraction and cosine similarity.

### External Editable Dependencies

- `videre` (at `../videre`) — video extraction
- `skullite` (at `../skullite`) — SQLite wrapper (`PysaurusConnection(None)` = in-memory DB; `copy_from()` = bulk copy)

### PySide6 Conventions (`interface/pyside6/`)

PySide6 is the primary GUI frontend. Unlike web frontends, it does **not** go through `FeatureAPI`. Instead, all calls go through the **`AppContext` facade** — pages and dialogs must never access internal attributes (`_database`, `_ops`, `_algos`, `_provider`) directly.

#### Auto-refresh via `state_changed` signal

- Every **state-mutating** facade method in `AppContext` must emit `self.state_changed.emit()` after the backend call. `MainWindow._on_state_changed()` then refreshes the active page automatically.
- Manual `self.refresh()` calls in pages are reserved for **UI-only changes** (pagination, toggle view). Never use manual `refresh()` after a backend state change — rely on the signal.

#### Backend notification

- Every backend write operation (in `AbstractDatabase`, `DatabaseOperations`, `DatabaseAlgorithms`) must call `_notify_fields_modified(fields, is_property)` so the `VideoProvider` stays synchronized. Without this, grouping/filtering can become stale.

#### Double-execution protection

- Persistent buttons (toolbar, sidebar, dialogs) that trigger **non-idempotent** operations must be disabled during execution:
  ```python
  def _on_action(self):
      self.btn.setEnabled(False)
      try:
          # ... backend operation ...
      finally:
          self.btn.setEnabled(True)
  ```
- Context menu actions don't need this — the menu closes on first click.
- Long operations use `_run_process()` which shows a `ProcessPage` blocking all interaction. A guard (`if self._process_page is not None: return`) prevents concurrent processes.

#### Batch operations

- When performing multiple write operations in a loop (e.g., deleting N videos), wrap them in `with db.to_save():` to batch saves into a single operation, and emit `state_changed` once after the loop.

## Code Style

- **Formatter/Linter**: Ruff (`skip-magic-trailing-comma = true`)
- **Python version**: 3.13 (strict: `>=3.13,<3.14`)
- Unused imports allowed in `__init__.py` files (ruff F401 ignored)

## Testing

- pytest with `asyncio_mode = "auto"`
- Test fixtures provide three tiers:
  - **Fast mock**: `mock_database` / `mock_database_readonly` — pure in-memory, no I/O (data from `tests/mocks/test_data.json`)
  - **Writable copies**: `mem_old_database`, `mem_saurus_database`, `example_*_memory` — `shutil.copytree` to `tmp_path`
  - **Read-only on-disk**: `fake_old_database`, `fake_saurus_database`, `example_json_database`, `example_saurus_database`
- SQL fixtures use `PysaurusConnection(None)` + `copy_from()` to create writable in-memory copies without `tmp_path`
- Two test databases in `tests/home_dir_test/.Pysaurus/databases/`: `test_database` (small) and `example_db_in_pysaurus` (90 videos with properties)
- Qt tests use `QT_QPA_PLATFORM=offscreen` (set in `tests/interface/pyside6_interface/conftest.py`)
- `pyfakefs` for filesystem mocking, `pytest-qt` for Qt tests, `pytest-xdist` for parallel runs
