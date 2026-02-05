from typing import Literal, Sequence, overload

from pysaurus.video.video_pattern import VideoPattern
from saurus.sql.pysaurus_connection import PysaurusConnection
from saurus.sql.sql_utils import SQLWhereBuilder
from saurus.sql.sql_video_wrapper import FORMATTED_VIDEO_TABLE_FIELDS
from saurus.sql.video_mega_utils import _get_videos
from saurus.sql.video_parser import FieldQuery, VideoFieldQueryParser

# Fields that require joining video_thumbnail table
_THUMBNAIL_FIELDS = frozenset({"thumbnail", "with_thumbnails"})


def _build_where_clause(
    where: dict | None,
) -> tuple[SQLWhereBuilder, FieldQuery | None]:
    """Build WHERE clause from dict, returning builder and video_id query if present."""
    where_builder = SQLWhereBuilder()
    selection_builder = SQLWhereBuilder(use_or=True)
    vid_query = None
    parser = VideoFieldQueryParser()
    seen = set()
    for key, value in (where or {}).items():
        parsed = parser.parse(key, value)
        if parsed.field in seen:
            raise ValueError(f"Duplicate field in where clause: {parsed.field}")
        seen.add(parsed.field)
        if parsed.field in ("video_id", "filename"):
            builder = selection_builder
            if parsed.field == "video_id":
                vid_query = parsed
        else:
            builder = where_builder
        builder.append_field_query(parsed)
    if selection_builder:
        where_builder.append_query_builder(selection_builder)
    return where_builder, vid_query


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


@overload
def video_mega_search(
    db: PysaurusConnection,
    *,
    include: Sequence[str] | None = None,
    with_moves: bool = False,
    where: dict | None = None,
    # Optimization flags
    count_only: Literal[False] = False,
    exists_only: Literal[True],
    ids_only: Literal[False] = False,
) -> bool: ...


@overload
def video_mega_search(
    db: PysaurusConnection,
    *,
    include: Sequence[str] | None = None,
    with_moves: bool = False,
    where: dict | None = None,
    # Optimization flags
    count_only: Literal[True],
    exists_only: Literal[False] = False,
    ids_only: Literal[False] = False,
) -> int: ...


@overload
def video_mega_search(
    db: PysaurusConnection,
    *,
    include: Sequence[str] | None = None,
    with_moves: bool = False,
    where: dict | None = None,
    # Optimization flags
    count_only: Literal[False] = False,
    exists_only: Literal[False] = False,
    ids_only: Literal[True],
) -> list[int]: ...


@overload
def video_mega_search(
    db: PysaurusConnection,
    *,
    include: Sequence[str] | None = None,
    with_moves: bool = False,
    where: dict | None = None,
    # Optimization flags
    count_only: Literal[False] = False,
    exists_only: Literal[False] = False,
    ids_only: Literal[False] = False,
) -> list[VideoPattern]: ...


def video_mega_search(
    db: PysaurusConnection,
    *,
    include: Sequence[str] | None = None,
    with_moves: bool = False,
    where: dict | None = None,
    # Optimization flags
    count_only: bool = False,
    exists_only: bool = False,
    ids_only: bool = False,
) -> list[VideoPattern] | int | bool | list[int]:
    """
    Search for videos with various optimization modes.

    Args:
        db: Database connection
        include: Fields to include in results. None means all fields.
        with_moves: Whether to include move information
        where: Filter conditions
        count_only: If True, return only the count (int)
        exists_only: If True, return whether any match exists (bool)
        ids_only: If True, return only video IDs (list[int])

    Returns:
        Depending on flags:
        - exists_only=True: bool
        - count_only=True: int
        - ids_only=True: list[int]
        - Otherwise: list[VideoPattern]
    """
    where_builder, vid_query = _build_where_clause(where)
    where_clause = where_builder.get_where_clause()
    params = where_builder.get_parameters()

    # Check if we need thumbnail join for the where clause
    needs_thumbnail_for_where = _needs_thumbnail_join(None, where)

    # Fast path: exists_only - just check if any row matches
    if exists_only:
        if needs_thumbnail_for_where:
            query = f"""
            SELECT 1 FROM video AS v
            LEFT JOIN video_thumbnail AS t ON v.video_id = t.video_id
            {where_clause} LIMIT 1
            """
        else:
            query = f"SELECT 1 FROM video AS v {where_clause} LIMIT 1"
        result = db.query_one(query, params)
        return result is not None

    # Fast path: count_only - just count matching rows
    if count_only:
        if needs_thumbnail_for_where:
            query = f"""
            SELECT COUNT(v.video_id) FROM video AS v
            LEFT JOIN video_thumbnail AS t ON v.video_id = t.video_id
            {where_clause}
            """
        else:
            query = f"SELECT COUNT(v.video_id) FROM video AS v {where_clause}"
        result = db.query_one(query, params)
        return result[0] if result else 0

    # Fast path: ids_only - return just video IDs
    if ids_only:
        query_with = ""
        query_with_join = ""
        query_order = ""
        if vid_query and len(vid_query.values) > 1:
            query_with = (
                f"WITH vid_order(video_id, rank) AS "
                f"(VALUES {','.join(f'({v},{r})' for r, v in enumerate(vid_query.values))})"
            )
            query_with_join = "LEFT JOIN vid_order AS vo ON v.video_id = vo.video_id"
            query_order = "ORDER BY vo.rank"
        query = f"""
        {query_with}
        SELECT v.video_id FROM video AS v
        {query_with_join}
        {where_clause}
        {query_order}
        """
        return [row[0] for row in db.query(query, params)]

    # Standard path: full video search
    needs_thumbnail = _needs_thumbnail_join(include, where)

    query_with = ""
    query_with_join = ""
    query_with_order = ""
    if vid_query and len(vid_query.values) > 1:
        query_with = (
            f"WITH vid_order(video_id, rank) AS "
            f"(VALUES {','.join(f'({v},{r})' for r, v in enumerate(vid_query.values))})"
        )
        query_with_join = "LEFT JOIN vid_order AS vo ON v.video_id = vo.video_id"
        query_with_order = "ORDER BY vo.rank"

    if needs_thumbnail:
        query = f"""
        {query_with}
        SELECT
            {FORMATTED_VIDEO_TABLE_FIELDS},
            t.thumbnail AS thumbnail,
            IIF(LENGTH(t.thumbnail), 1, 0) AS with_thumbnails
        FROM video AS v LEFT JOIN video_thumbnail AS t
        ON v.video_id = t.video_id
        {query_with_join}
        {where_clause}
        {query_with_order}
        """
    else:
        query = f"""
        {query_with}
        SELECT
            {FORMATTED_VIDEO_TABLE_FIELDS},
            NULL AS thumbnail,
            0 AS with_thumbnails
        FROM video AS v
        {query_with_join}
        {where_clause}
        {query_with_order}
        """

    return _get_videos(db, query, params, include=include, with_moves=with_moves)
