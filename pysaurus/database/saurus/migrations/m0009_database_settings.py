"""Migration to version 9: per-database settings on the collection row.

First setting: the property that "Generalize title" targets without asking.
Stored as a foreign key, so it follows a rename and clears itself when the
property is deleted. ``ALTER TABLE ADD COLUMN`` accepts a REFERENCES clause as
long as the default is NULL, which it is.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skullite import Skullite


def migrate(db: Skullite) -> None:
    with db.connect() as connection:
        existing = {
            row["name"] for row in connection.query_all("PRAGMA table_info(collection)")
        }
        if "generalize_title_property_id" not in existing:
            connection.modify(
                "ALTER TABLE collection ADD COLUMN generalize_title_property_id INTEGER"
                " REFERENCES property(property_id) ON DELETE SET NULL"
            )
