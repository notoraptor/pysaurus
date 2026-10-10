"""Migration to version 11: saved searches.

Searchexp expressions the user asked the database to remember, each under an
optional unique name. The expression is the identity: saving it again renames
it. Stored as text, so a search naming a property breaks when that property is
renamed or deleted; it is kept and fails when applied.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skullite import Skullite


def migrate(db: Skullite) -> None:
    with db.connect() as connection:
        connection.modify(
            "CREATE TABLE IF NOT EXISTS saved_search ("
            "expression TEXT PRIMARY KEY NOT NULL, name TEXT UNIQUE)"
        )
