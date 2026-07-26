"""Migration to version 5: hold bool properties to their two-value domain.

A bool property is now always unique, and never spells its domain out in
``property_enumeration`` -- that table holds only its default value (the
domain is derived by ``PropType.possible_values``). ``PropType.__init__``
refuses anything else, so a database that predates the rule would become
unreadable; this migration brings it in line first, then adds a CHECK
constraint so no future write can break the invariant again.

SQLite cannot add a CHECK with ``ALTER TABLE``, so the ``property`` table is
rebuilt, same pattern as m0003/m0004.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skullite import Skullite

# Distinctive substring of the new CHECK, used to detect whether the table
# was already rebuilt.
_BOOL_CHECK_MARKER = "type != 'bool'"


def _bool_property_ids(db: Skullite, *, multiple: bool | None = None) -> list[int]:
    clause = "SELECT property_id FROM property WHERE type = 'bool'"
    if multiple is not None:
        clause += f" AND multiple = {int(multiple)}"
    with db.connect() as connection:
        return [row["property_id"] for row in connection.query_all(clause)]


def _collapse_multiple_bools(db: Skullite, property_id: int) -> None:
    """Keep a single value per video for a bool that was wrongly multiple.

    A video carrying both values means "the whole domain", which says nothing;
    True wins (MAX over the stored "0"/"1" text) so the outcome is at least
    deterministic. No UI ever allowed this, so in practice there is nothing
    to collapse -- this only guards hand-made databases.

    The keeper is correlated on the *outer* video_id, spelled in full: an
    unqualified `video_id` would bind to the inner `keeper` instead, making the
    condition a tautology and MAX a per-property maximum, which would delete
    every False of every video as soon as one video held True.
    """
    with db.connect() as connection:
        connection.modify(
            "DELETE FROM video_property_value "
            "WHERE property_id = ? AND property_value NOT IN ("
            "    SELECT MAX(property_value) FROM video_property_value AS keeper"
            "    WHERE keeper.property_id = ?"
            "      AND keeper.video_id = video_property_value.video_id"
            ")",
            [property_id, property_id],
        )


def _normalize_bool_properties(db: Skullite) -> None:
    """Make every bool property unique, with exactly one enumeration row."""
    # Only a bool that was declared multiple can hold several values per video.
    # A unique one already has at most one, so it must be left untouched.
    for property_id in _bool_property_ids(db, multiple=True):
        _collapse_multiple_bools(db, property_id)
    for property_id in _bool_property_ids(db):
        with db.connect() as connection:
            # Only the default value (rank 0) is kept: the domain is implicit.
            connection.modify(
                "DELETE FROM property_enumeration WHERE property_id = ? AND rank > 0",
                [property_id],
            )
            # A property with no row at all would break prop_type_search, which
            # reads the default as enumeration[0]; seed False in that case.
            rows = connection.query_all(
                "SELECT COUNT(*) AS nb FROM property_enumeration WHERE property_id = ?",
                [property_id],
            )
            if not rows[0]["nb"]:
                connection.modify(
                    "INSERT INTO property_enumeration (property_id, enum_value, rank) "
                    "VALUES (?, '0', 0)",
                    [property_id],
                )
    with db.connect() as connection:
        connection.modify("UPDATE property SET multiple = 0 WHERE type = 'bool'")


def _needs_rebuild(db: Skullite) -> bool:
    """Return True unless the property table already carries the new CHECK."""
    with db.connect() as connection:
        rows = connection.query_all(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='property'"
        )
    if not rows:
        return False  # No property table yet: database.sql will create it right.
    return _BOOL_CHECK_MARKER not in rows[0]["sql"]


def _rebuild_property_table(db: Skullite) -> None:
    """Rebuild the property table with the bool CHECK.

    Foreign keys are turned off so DROP does not cascade-delete the rows of
    property_enumeration and video_property_value. The video_property_text
    view is dropped first: it selects from property, and SQLite refuses to
    rename a table while a view referencing a missing one exists. Both it and
    any lost trigger are recreated right after by _run_schema_script().
    """
    with db.connect() as connection:
        connection.modify("PRAGMA foreign_keys = OFF")
        connection.modify("DROP VIEW IF EXISTS video_property_text")
        connection.script(_CREATE_PROPERTY_TABLE_NEW)
        connection.modify(
            "INSERT INTO _property_new (property_id, name, type, multiple) "
            "SELECT property_id, name, type, multiple FROM property"
        )
        connection.modify("DROP TABLE property")
        connection.modify("ALTER TABLE _property_new RENAME TO property")
        connection.modify("PRAGMA foreign_keys = ON")


def migrate(db: Skullite) -> None:
    _normalize_bool_properties(db)
    if _needs_rebuild(db):
        _rebuild_property_table(db)


# Must stay in sync with the property table in database.sql.
_CREATE_PROPERTY_TABLE_NEW = """\
CREATE TABLE _property_new (
	property_id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	type TEXT NOT NULL,
	multiple INTEGER NOT NULL DEFAULT 0,
	CHECK (type IN ("bool", "int", "float", "str")),
	CHECK (multiple IN (0, 1)),
	-- A bool is its own two-value domain, so it can only ever hold one value.
	CHECK (type != 'bool' OR multiple = 0),
	UNIQUE (name)
);
"""
