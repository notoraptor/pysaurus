# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tools

- Prefer the LSP tool over Grep for Python symbol searches (references, definitions, usages). Fetch it via ToolSearch if needed.

## Project

Pysaurus is a video collection manager (WIP) written in Python 3.13. It handles video metadata extraction, custom properties, advanced search/filtering, video similarity detection, with a PySide6 (Qt) GUI.

## Commands

All commands must be run with `uv run`:

```bash
# Run the application
uv run -m pysaurus

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

# Type check (full project, all packages)
uv run ty check

# Type check (subset used by CI — excludes pyside6/)
uv run poe typecheck

# Run all checks (format + lint + typecheck subset)
uv run poe check
```

## Architecture

### High-level Flow

```
__main__.py
    → PySide6 GUI
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

`pysaurus/__main__.py` — launches the PySide6 GUI directly.

### Database Layer

Layered separation of concerns:
- **`database/abstract_database.py`** — abstract interface (~35 methods)
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
- `video` table uses **virtual generated columns** (e.g., `readable`, `found`, `length_seconds`, `byte_rate`, `day`, `year`)
- `video_text` is an **FTS5 virtual table** for full-text search with triggers to stay in sync
- Property value triggers are managed manually in Python (not SQL triggers) for batch performance

### View Layer (`dbview/`)

- **`view_context.py`** — `ViewContext`: pure state holder for view parameters (sources, grouping, classifier, group, search, sorting). Owned by the API/interface layer, passed to `db.query_videos()`.
- **`view_tools.py`** — `GroupDef`, `SearchDef`
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

### Shared UI-side helpers (`interface/common/`)

- **`common.py`** — `FieldInfo`, `FieldType`, `GroupPerm` enums used by GUI code to describe video fields (sortability, grouping permissions).
- **`qt_utils.py`** — small Qt helpers shared by PySide6 pages/dialogs.

### Notification System

Python backend sends typed `Notification` objects — `DatabaseReady`, `Done`, etc. in `pysaurus/core/notifications.py`; `JobToDo`, `JobStep` in `pysaurus/core/job_notifications.py`.

### GUI

PySide6 is the only active GUI. Legacy interfaces (Flask, pywebview, qtwebview, React web frontend) have been moved to `wip/pysaurus_interfaces/` and are no longer part of the active codebase.

### Expression Search (external `searchexp` package, at `../searchexp`)

Standalone parser for structured search expressions (e.g. `width > 1080 and "eng" in audio_languages`). Lives in its own repo (`../searchexp`, editable dep) — no references to `VideoPattern` or database internals.

- **`ExpressionParser`** — receives `attributes` and/or `properties` dicts (`{name: FieldType}`), parses an expression string into an IR (AST)
- **`fields_from_class()`** — helper to introspect a class's annotations into a `dict[str, FieldType]`
- **IR nodes** — frozen dataclasses: `FieldRef`, `LiteralValue`, `Comparison`, `IsOp`, `InOp`, `LogicalOp`, `NotOp`, `FunctionCall`, `SetLiteral`
- Pysaurus-side integration notes: `docs/pysaurus_with_searchexp.md`. Language design/spec lives with the package (`../searchexp/docs/`).

### Properties System

`properties/properties.py` — typed property definitions (bool, int, float, str) with support for multiple values and enumeration.

### Image Similarity Search

`imgsimsearch/` — uses NumPy for feature extraction and cosine similarity.

### External Editable Dependencies

- `videre` (at `../videre`) — video extraction
- `skullite` (at `../skullite`) — SQLite wrapper (`PysaurusConnection(None)` = in-memory DB; `copy_from()` = bulk copy)

### PySide6 Conventions (`interface/pyside6/`)

PySide6 is the only GUI frontend. All calls go through the **`AppContext` facade** — pages and dialogs must never access internal attributes (`_database`, `_ops`, `_algos`, `_view`) directly.

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
- Test fixtures (all defined in `tests/conftest.py`):
  - **Fast mock**: `mock_database` — pure in-memory mock, no I/O (data from `tests/mocks/test_data.json`)
  - **Saurus SQL, test_database** (small): `fake_saurus_database` and `mem_saurus_database` — both in-memory copies via `PysaurusConnection(None)` + `copy_from()`; identical for SQL since every fixture is an in-memory copy, so there is no separate read-only/writable pair
  - **Saurus SQL, example_db_in_pysaurus** (90 videos with properties): `example_saurus_database` (read-only, on-disk) and `example_saurus_database_memory` (in-memory copy for writes)
- SQL fixtures do not need `tmp_path` — in-memory SQLite is used directly
- Two test databases in `tests/home_dir_test/.Pysaurus/databases/`: `test_database` (small) and `example_db_in_pysaurus` (90 videos with properties)
- Qt tests use `QT_QPA_PLATFORM=offscreen` (set in `tests/interface/pyside6_interface/conftest.py`)
- `pyfakefs` for filesystem mocking, `pytest-qt` for Qt tests, `pytest-xdist` for parallel runs
