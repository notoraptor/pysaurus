"""Migration to version 7: store pixel aspect ratio and display rotation.

``width``/``height`` are storage dimensions. What a player shows can differ
for two independent reasons: a sample aspect ratio other than 1/1 (anamorphic
content -- DVD, DVB, older MP4), and a display matrix (phone videos shot in
portrait). Both are now captured at collect time.

Existing rows keep the neutral values (SAR 1/1, no rotation) until their video
is scanned again, which is also what an unreadable video gets.

``display_width``/``display_height`` derive the on-screen size from them, so a
1920x1080 video carrying a 90 degrees rotation reads as 1080x1920 -- the size
VLC and the thumbnail both show.

Every column is either plain or VIRTUAL, both of which ``ALTER TABLE ADD
COLUMN`` accepts -- no table rebuild. Order matters: a generated column can
only reference columns the table already has.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skullite import Skullite

_NEW_COLUMNS = (
    ("rotation", "INTEGER NOT NULL DEFAULT 0"),
    ("sample_aspect_ratio_den", "INTEGER NOT NULL DEFAULT 1"),
    ("sample_aspect_ratio_num", "INTEGER NOT NULL DEFAULT 1"),
    (
        "_unsquished_width",
        "INTEGER GENERATED ALWAYS AS ("
        "IIF("
        "sample_aspect_ratio_num > 0 AND sample_aspect_ratio_den > 0, "
        "(width * sample_aspect_ratio_num + sample_aspect_ratio_den / 2)"
        " / sample_aspect_ratio_den, "
        "width"
        ")"
        ") VIRTUAL",
    ),
    (
        "display_width",
        "INTEGER GENERATED ALWAYS AS "
        "(IIF(rotation % 180 = 0, _unsquished_width, height)) VIRTUAL",
    ),
    (
        "display_height",
        "INTEGER GENERATED ALWAYS AS "
        "(IIF(rotation % 180 = 0, height, _unsquished_width)) VIRTUAL",
    ),
)


def migrate(db: Skullite) -> None:
    with db.connect() as connection:
        existing = {
            row["name"] for row in connection.query_all("PRAGMA table_xinfo(video)")
        }
        for name, definition in _NEW_COLUMNS:
            if name not in existing:
                connection.modify(f"ALTER TABLE video ADD COLUMN {name} {definition}")
