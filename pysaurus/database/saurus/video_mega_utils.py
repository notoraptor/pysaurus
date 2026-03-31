from collections import defaultdict
from typing import Iterable, Sequence

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.database.saurus.prop_type_search import prop_type_search
from pysaurus.database.saurus.pysaurus_connection import PysaurusConnection
from pysaurus.database.saurus.sql_utils import sql_placeholders
from pysaurus.database.saurus.sql_video_wrapper import SQLVideoWrapper
from pysaurus.properties.properties import PropType


def _get_videos(
    db: PysaurusConnection,
    query: str,
    parameters: Sequence,
    *,
    include: Sequence[str] | None = None,
    with_moves: bool = False,
) -> list[SQLVideoWrapper]:
    with db:
        videos = [SQLVideoWrapper(row) for row in db.query(query, parameters)]

    # Early return if no videos or minimal include (no extra data needed)
    if not videos:
        return videos

    include_set = set(include) if include is not None else None

    # Determine what extra data we need to fetch
    with_errors = include_set is None or "errors" in include_set
    with_audio_languages = include_set is None or "audio_languages" in include_set
    with_subtitle_languages = include_set is None or "subtitle_languages" in include_set
    with_properties = include_set is None or "properties" in include_set

    # Fast path: if we only need basic video fields, skip all extra queries
    if not (
        with_errors
        or with_audio_languages
        or with_subtitle_languages
        or with_properties
        or with_moves
    ):
        return videos

    video_ids = [video.video_id for video in videos]
    placeholders = sql_placeholders(len(video_ids))

    errors = defaultdict(list)
    languages = {"a": defaultdict(list), "s": defaultdict(list)}
    properties = defaultdict(dict)
    json_properties = {}

    if with_errors:
        with db:
            for row in db.query(
                f"SELECT video_id, error FROM video_error "
                f"WHERE video_id IN ({placeholders})",
                video_ids,
            ):
                errors[row[0]].append(row[1])
    if with_audio_languages or with_subtitle_languages:
        with db:
            for row in db.query(
                f"SELECT stream, video_id, lang_code FROM video_language "
                f"WHERE video_id IN ({placeholders}) "
                f"ORDER BY stream ASC, video_id ASC, rank ASC",
                video_ids,
            ):
                languages[row[0]][row[1]].append(row[2])
    if with_properties:
        prop_types: dict[int | None, PropType] = {
            pt.property_id: pt for pt in prop_type_search(db)
        }
        with db:
            for row in db.query(
                f"SELECT video_id, property_id, property_value "
                f"FROM video_property_value WHERE video_id IN ({placeholders})",
                video_ids,
            ):
                properties[row[0]].setdefault(row[1], []).append(row[2])
        json_properties = {
            video_id: {
                prop_types[property_id].name: prop_types[property_id].from_strings(
                    values
                )
                for property_id, values in raw_properties.items()
            }
            for video_id, raw_properties in properties.items()
        }

    if with_errors:
        for video in videos:
            video.errors = errors.get(video.video_id, [])
    if with_audio_languages:
        for video in videos:
            video.audio_languages = languages["a"].get(video.video_id, [])
    if with_subtitle_languages:
        for video in videos:
            video.subtitle_languages = languages["s"].get(video.video_id, [])
    if with_properties:
        for video in videos:
            video.properties = json_properties.get(video.video_id, {})
    if with_moves:
        moves = {
            video_id: video_moves for video_id, video_moves in _get_video_moves(db)
        }
        for video in videos:
            video.moves = moves.get(video.video_id, [])

    return videos


def _get_video_moves(db: PysaurusConnection) -> Iterable[tuple[int, list[dict]]]:
    # Optimized: avoids GROUP_CONCAT which can produce multi-MB strings.
    # Uses a structured query with window functions instead.
    with db:
        current_group = None
        not_found = []
        found = []

        for row in db.query(
            """
            WITH move_groups AS (
                SELECT
                    video_id,
                    is_file,
                    filename,
                    file_size,
                    duration,
                    duration_time_base_not_null,
                    COUNT(*) OVER (PARTITION BY file_size, duration, duration_time_base_not_null) as group_count,
                    SUM(is_file) OVER (PARTITION BY file_size, duration, duration_time_base_not_null) as found_count
                FROM video
                WHERE unreadable = 0 AND discarded = 0
            )
            SELECT video_id, is_file, filename, file_size, duration, duration_time_base_not_null
            FROM move_groups
            WHERE group_count > 1 AND found_count > 0 AND found_count < group_count
            ORDER BY file_size, duration, duration_time_base_not_null, is_file DESC
            """
        ):
            group_key = (
                row[3],
                row[4],
                row[5],
            )  # file_size, duration, duration_time_base_not_null

            # New group detected
            if current_group != group_key:
                # Emit previous group if it exists
                if current_group is not None and not_found and found:
                    for id_not_found in not_found:
                        yield id_not_found, found

                # Reset for new group
                current_group = group_key
                not_found = []
                found = []

            # Accumulate videos for current group
            video_id = row[0]
            is_file = row[1]
            filename = row[2]

            if is_file:
                found.append(
                    {
                        "video_id": video_id,
                        "filename": AbsolutePath(filename).standard_path,
                    }
                )
            else:
                not_found.append(video_id)

        # Emit last group
        if current_group is not None and not_found and found:
            for id_not_found in not_found:
                yield id_not_found, found
