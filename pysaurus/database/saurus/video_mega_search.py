from typing import Sequence

from pysaurus.database.saurus.pysaurus_connection import PysaurusConnection
from pysaurus.database.saurus.sql_utils import SQLWhereBuilder
from pysaurus.database.saurus.sql_video_wrapper import FORMATTED_VIDEO_TABLE_FIELDS
from pysaurus.database.saurus.video_mega_utils import _get_videos
from pysaurus.database.saurus.video_parser import VideoFieldQueryParser
from pysaurus.video.video_pattern import VideoPattern

# Fields that require joining video_thumbnail table
_THUMBNAIL_FIELDS = frozenset({"thumbnail", "with_thumbnails"})


def _build_where_clause(where: dict | None) -> SQLWhereBuilder:
    """Build WHERE clause from dict."""
    where_builder = SQLWhereBuilder()
    selection_builder = SQLWhereBuilder(use_or=True)
    parser = VideoFieldQueryParser()
    seen = set()
    for key, value in (where or {}).items():
        parsed = parser.parse(key, value)
        if parsed.field in seen:
            raise ValueError(f"Duplicate field in where clause: {parsed.field}")
        seen.add(parsed.field)
        if parsed.field in ("video_id", "filename"):
            builder = selection_builder
        else:
            builder = where_builder
        builder.append_field_query(parsed)
    if selection_builder:
        where_builder.append_query_builder(selection_builder)
    return where_builder


def _needs_thumbnail_join(include: Sequence[str] | None, where: dict | None) -> bool:
    """Check if we need to JOIN video_thumbnail table."""
    if include is None:
        return True
    if set(include) & _THUMBNAIL_FIELDS:
        return True
    # Check if where clause references thumbnail fields
    if where:
        if "with_thumbnails" in where or "without_thumbnails" in where:
            return True
    return False


def video_mega_exists(db: PysaurusConnection, *, where: dict | None = None) -> bool:
    """Check if any video matches the given filters."""
    where_builder = _build_where_clause(where)
    where_clause = where_builder.get_where_clause()
    params = where_builder.get_parameters()

    needs_thumbnail = _needs_thumbnail_join(None, where)
    if needs_thumbnail:
        query = f"""
        SELECT 1 FROM video AS v
        LEFT JOIN video_thumbnail AS t ON v.video_id = t.video_id
        {where_clause} LIMIT 1
        """
    else:
        query = f"SELECT 1 FROM video AS v {where_clause} LIMIT 1"
    result = db.query_one(query, params)
    return result is not None


def video_mega_count(db: PysaurusConnection, *, where: dict | None = None) -> int:
    """Count videos matching the given filters."""
    where_builder = _build_where_clause(where)
    where_clause = where_builder.get_where_clause()
    params = where_builder.get_parameters()

    needs_thumbnail = _needs_thumbnail_join(None, where)
    if needs_thumbnail:
        query = f"""
        SELECT COUNT(v.video_id) FROM video AS v
        LEFT JOIN video_thumbnail AS t ON v.video_id = t.video_id
        {where_clause}
        """
    else:
        query = f"SELECT COUNT(v.video_id) FROM video AS v {where_clause}"
    result = db.query_one(query, params)
    return result[0] if result else 0


def video_mega_search(
    db: PysaurusConnection,
    *,
    include: Sequence[str] | None = None,
    with_moves: bool = False,
    where: dict | None = None,
) -> list[VideoPattern]:
    """Search for videos, returning full VideoPattern objects."""
    where_builder = _build_where_clause(where)
    where_clause = where_builder.get_where_clause()
    params = where_builder.get_parameters()

    needs_thumbnail = _needs_thumbnail_join(include, where)

    if needs_thumbnail:
        query = f"""
        SELECT
            {FORMATTED_VIDEO_TABLE_FIELDS},
            t.thumbnail AS thumbnail,
            IIF(LENGTH(t.thumbnail), 1, 0) AS with_thumbnails
        FROM video AS v LEFT JOIN video_thumbnail AS t
        ON v.video_id = t.video_id
        {where_clause}
        """
    else:
        query = f"""
        SELECT
            {FORMATTED_VIDEO_TABLE_FIELDS},
            NULL AS thumbnail,
            0 AS with_thumbnails
        FROM video AS v
        {where_clause}
        """

    return _get_videos(db, query, params, include=include, with_moves=with_moves)
