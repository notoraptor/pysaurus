"""Migration to version 10: second database setting.

Whether "Copy similarity infos" overwrites a unique property already valued on
the destination video. A plain boolean column, off by default.
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
        if "copy_overwrites_unique_properties" not in existing:
            connection.modify(
                "ALTER TABLE collection ADD COLUMN copy_overwrites_unique_properties"
                " INTEGER NOT NULL DEFAULT 0"
            )
