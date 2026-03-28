# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tools

- Prefer the LSP tool over Grep for Python symbol searches (references, definitions, usages). Fetch it via ToolSearch if needed.

## Project

Pysaurus is a video collection manager (WIP) written in Python 3.13. It handles video metadata extraction, custom properties, advanced search/filtering, video similarity detection, and supports multiple GUI frontends.

## Commands

All commands must be run with `uv run`:

```bash
# Run the application (default GUI: pyside6)
uv run -m pysaurus
uv run -m pysaurus pyside6   # or: flask, flaskview, pywebview, qtwebview

# Run CLI (benchmark/debug console, configured via .pysaurus.yaml)
uv run -m pysaurus.interface.console.run --db <name>

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

# Type check
uv run mypy pysaurus/

# Run all checks (format + lint + mypy)
uv run poe check
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
__main__.py (GUI selector, default: pyside6)
    → Interface Layer (PySide6 / PyWebView / QtWebView)
        → GuiAPI / FeatureAPI (proxy-based API)
            ├─ .view → ViewContext (filtering/grouping state)
            └─ → AbstractDatabase
                 ├─ .ops → DatabaseOperations (CRUD)
                 ├─ .algos → DatabaseAlgorithms (batch processing)
                 └─ .query_videos(view, ...) → VideoSearchContext
```

### Package Structure

Single top-level package **`pysaurus/`** containing all application code, including the SQL layer at `pysaurus/database/saurus/`.

### Entry Point

`pysaurus/__main__.py` — selects GUI at runtime based on CLI argument (`pyside6`, `flask`, `flaskview`, `pywebview`, `qtwebview`). Default: `pyside6`.

### Database Layer

Layered separation of concerns:
- **`database/abstract_database.py`** — minimal abstract interface (~20 methods)
- **`database/database_operations.py`** — high-level CRUD operations (accessed via `db.ops`)
- **`database/database_algorithms.py`** — batch processing: update, miniatures, moves (accessed via `db.algos`)

Single backend implementation:
- **`database/saurus/pysaurus_collection.py`** — SQLite implementation (uses `skullite` wrapper)
- **`database/database.py`** — exposes `Database = PysaurusCollection`

### SQL Layer (`database/saurus/`)

- **`pysaurus_collection.py`** — implements `AbstractDatabase` with SQLite
- **`pysaurus_connection.py`** — extends `Skullite` (from `skullite` package), loads schema from `database.sql`
- **`video_mega_group.py` / `video_mega_search.py`** — SQL query builders for grouping and search
Key schema notes (`database/saurus/database.sql`):
- `video` table uses **virtual generated columns** (e.g., `readable`, `found`, `length_seconds`, `bit_rate`, `day`, `year`)
- `video_text` is an **FTS5 virtual table** for full-text search with triggers to stay in sync
- Property value triggers are managed manually in Python (not SQL triggers) for batch performance

### View Layer (`dbview/`)

- **`view_context.py`** — `ViewContext`: pure state holder for view parameters (sources, grouping, classifier, group, search, sorting). Owned by the API/interface layer, passed to `db.query_videos()`.
- **`view_tools.py`** — `GroupDef`, `SearchDef`, `LookupArray`, etc.
- **`view_utils.py`** — `parse_sources()`, `parse_sorting()`
- **`field_stat.py`** — statistics for field groups

Each interface owns a `ViewContext` and mutates it (`view.set_search(...)`, `view.set_grouping(...)`, etc.), then calls `db.query_videos(view, page_size, page)` to get a `VideoSearchContext`.

### API Layer — Proxy Pattern (`interface/api/`)

All frontends call `api.__run_feature__(name, *args)`, which looks up a proxy dict, then falls back to calling `self.<name>(*args)` directly.

**`ProxyFeature`** (`api_utils/proxy_feature.py`) wraps `(getter_fn, method, returns_value)`:
1. Calls `getter()` to get the live target (db, app, etc.)
2. Calls `getattr(target, method.__name__)(*args)`
3. Returns the result only if `returns=True`; otherwise returns `None` (side-effect only)

Proxy subclasses and their targets:

| Class | Target | Use case |
|---|---|---|
| `FromDb` | `api.database` | Direct `AbstractDatabase` methods |
| `FromApp` | `api.application` | `Application` methods |
| `FromOps` | `DatabaseOperations(api.database)` | CRUD via `db.ops` |
| `FromAlgo` | `DatabaseAlgorithms(api.database)` | Batch processing via `db.algos` |
| `FromTk` | `filedial` module | File dialog calls |
| `FromPyperclip` | `pyperclip` module | Clipboard operations |

- **`FeatureAPI`** — base API class exposing 50+ features via these proxies. Owns a `ViewContext` (`self.view`) for view state management, with explicit view methods (set_sources, set_search, set_sort, set_groups, etc.).
- **`GuiAPI`** — extends `FeatureAPI` with Flask video server (`ServerLauncher`), thread management, VLC integration, and an abstract `_notify()` method each frontend implements.

### Notification System

Python backend sends typed `Notification` objects (`pysaurus/core/notifications.py`) — e.g., `DatabaseReady`, `Done`, `JobToDo`, `JobStep`. These are serialized to dicts and forwarded to the frontend via `window.NOTIFICATION_MANAGER.call(notification)`.

### GUI Frontends

| Name | Module | Mechanism | Status |
|---|---|---|---|
| `pyside6` | `pyside6/` | Native Qt widgets (no web) | Default / Primary |
| `flask` | `flask/` | Flask + Jinja2 server-side rendering, opens in browser | Active (fallback) |
| `flaskview` | `flask/` | Same as `flask` but in a `pywebview` desktop window | Active (fallback) |
| `pywebview` | `using_pywebview/` | Flask HTTP server + `webview` JS bridge | Legacy |
| `qtwebview` | `qtwebview/` | `PySide6.QtWebEngineWidgets` + `QWebChannel` | Legacy |

### Flask Interface (`interface/flask/`)

Lightweight web interface — server-side rendered, minimal JavaScript. Designed as a pure-Python fallback requiring no system dependencies (no Qt, no Node.js). See `docs/flask-design.md` for full design doc.

- **`FlaskContext`** — facade to `Application`/`AbstractDatabase`/`DatabaseOperations`/`DatabaseAlgorithms` (similar role to `AppContext` in PySide6)
- **Stateless view**: no persistent `ViewContext` — each request rebuilds an ephemeral `ViewContext` from URL query params (`_build_view()`)
- **Thumbnails**: loaded in a single SQL query per page, embedded as base64 data URIs (no separate `/thumbnail/<id>` route)
- **Long operations** (update, similarity search): run in a daemon thread, progress polled via JS every second
- **Does NOT use `FeatureAPI`** — calls `db.*`, `ops.*`, `algos.*` directly (no proxy system)
- Feature parity tracking: `docs/flask-vs-pyside6.md`

### Web Frontend (`interface/web/`)

- **Stack**: React 18, SystemJS, Babel (JSX transpilation), PropTypes
- **`BaseComponent`** (`src/BaseComponent.js`): base React component that auto-binds all methods and adds `setStateAsync()`
- **`Backend`** static class (`src/utils/backend.js`): all Python API calls go through `python_call(name, ...args)` → `window.backend_call(name, args)`. `backend_call` is injected by the runtime (CEF = `window.python.call`, Qt = QWebChannel `backend.call`)
- **Pages**: `DatabasesPage`, `HomePage`, `VideosPage`, `PropertiesPage`

### Expression Search (`core/searchexp/`)

Standalone parser for structured search expressions (e.g. `width > 1080 and "eng" in audio_languages`). Independent of Pysaurus — no references to `VideoPattern` or database internals.

- **`ExpressionParser`** — receives `attributes` and/or `properties` dicts (`{name: FieldType}`), parses an expression string into an IR (AST)
- **`fields_from_class()`** — helper to introspect a class's annotations into a `dict[str, FieldType]`
- **IR nodes** — frozen dataclasses: `FieldRef`, `LiteralValue`, `Comparison`, `IsOp`, `InOp`, `LogicalOp`, `NotOp`, `FunctionCall`, `SetLiteral`
- Design: `docs/searchexp.design.md` — Spec: `docs/searchexp.spec.md`

### Properties System

`properties/properties.py` — typed property definitions (bool, int, float, str) with support for multiple values and enumeration.

### Image Similarity Search

`imgsimsearch/` — uses NumPy for feature extraction and cosine similarity.

### External Editable Dependencies

- `videre` (at `../videre`) — video extraction
- `skullite` (at `../skullite`) — SQLite wrapper (`PysaurusConnection(None)` = in-memory DB; `copy_from()` = bulk copy)

### PySide6 Conventions (`interface/pyside6/`)

PySide6 is the primary GUI frontend. Unlike web frontends, it does **not** go through `FeatureAPI`. Instead, all calls go through the **`AppContext` facade** — pages and dialogs must never access internal attributes (`_database`, `_ops`, `_algos`, `_view`) directly.

#### Auto-refresh via `state_changed` signal

- Every **state-mutating** facade method in `AppContext` must emit `self.state_changed.emit()` after the backend call. `MainWindow._on_state_changed()` then refreshes the active page automatically.
- Manual `self.refresh()` calls in pages are reserved for **UI-only changes** (pagination, toggle view). Never use manual `refresh()` after a backend state change — rely on the signal.

#### Backend notification

- Every backend write operation (in `AbstractDatabase`, `DatabaseOperations`, `DatabaseAlgorithms`) must call `AbstractDatabase._notify_fields_modified(fields, is_property)` to save the database. All notification calls go through the single `_notify_fields_modified` on `AbstractDatabase` — there is no duplicate in `DatabaseOperations`. Since `query_videos()` is stateless, the next query will automatically pick up all changes.

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
- **No test coverage for the Flask interface** — changes to `pysaurus/interface/flask/` are not validated by existing tests
