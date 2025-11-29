from collections import defaultdict
from typing import Iterable, Sequence

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.properties.properties import PropTypeValidator
from pysaurus.video.video_pattern import VideoPattern
from saurus.sql.prop_type_search import prop_type_search
from saurus.sql.pysaurus_connection import PysaurusConnection
from saurus.sql.sql_video_wrapper import SQLVideoWrapper


def _get_videos(
    db: PysaurusConnection,
    query: str,
    parameters: Sequence,
    *,
    include: Sequence[str] | None = None,
    with_moves: bool = False,
) -> list[VideoPattern]:
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

    video_indices = [video.data["video_id"] for video in videos]
    placeholders = ", ".join(["?"] * len(video_indices))

    errors = defaultdict(list)
    languages = {"a": defaultdict(list), "s": defaultdict(list)}
    properties = defaultdict(dict)
    json_properties = {}

    if with_errors:
        for row in db.query(
            f"SELECT video_id, error FROM video_error "
            f"WHERE video_id IN ({placeholders})",
            video_indices,
        ):
            errors[row[0]].append(row[1])
    if with_audio_languages or with_subtitle_languages:
        for row in db.query(
            f"SELECT stream, video_id, lang_code FROM video_language "
            f"WHERE video_id IN ({placeholders}) "
            f"ORDER BY stream ASC, video_id ASC, rank ASC",
            video_indices,
        ):
            languages[row[0]][row[1]].append(row[2])
    if with_properties:
        prop_types: dict[int, PropTypeValidator] = {
            desc["property_id"]: PropTypeValidator(desc)
            for desc in prop_type_search(db)
        }
        for row in db.query(
            f"SELECT video_id, property_id, property_value "
            f"FROM video_property_value WHERE video_id IN ({placeholders})",
            video_indices,
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
    for row in db.query(
        """
    SELECT group_concat(video_id || '-' || is_file || '-' || hex(filename))
    FROM video
    WHERE unreadable = 0 AND discarded = 0
    GROUP BY file_size, duration, COALESCE(NULLIF(duration_time_base, 0), 1)
    HAVING COUNT(video_id) > 1 AND SUM(is_file) < COUNT(video_id);
    """
    ):
        not_found = []
        found = []
        for piece in row[0].split(","):
            str_video_id, str_is_file, str_hex_filename = piece.split("-")
            video_id = int(str_video_id)
            if int(str_is_file):
                found.append(
                    {
                        "video_id": video_id,
                        "filename": AbsolutePath(
                            bytes.fromhex(str_hex_filename).decode("utf-8")
                        ).standard_path,
                    }
                )
            else:
                not_found.append(video_id)
        assert not_found and found, (not_found, found)
        for id_not_found in not_found:
            yield id_not_found, found
