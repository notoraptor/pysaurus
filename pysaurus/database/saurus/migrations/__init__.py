"""Versioned migration system for the Saurus SQL database.

Each migration module must expose a ``migrate(db)`` function that receives
a :class:`~skullite.Skullite` instance and applies schema changes.

Migrations are keyed by their *target* version: migration N brings the
database from version N-1 to version N.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from skullite import Skullite

from pysaurus.database.saurus.migrations import (
    m0002_baseline,
    m0003_stored_filename_columns,
)

# Registry: target_version -> migrate(db) function.
# Migrations run in order for every version between current+1 and LATEST_VERSION.
MIGRATIONS: dict[int, Callable[[Skullite], None]] = {
    2: m0002_baseline.migrate,
    3: m0003_stored_filename_columns.migrate,
}

LATEST_VERSION: int = max(MIGRATIONS)
