from collections import defaultdict
from typing import Dict, List, Sequence

from pysaurus.properties.properties import PropTypeValidator
from saurus.sql.prop_type_search import prop_type_search
from saurus.sql.pysaurus_connection import PysaurusConnection
from saurus.sql.sql_video_wrapper import FORMATTED_VIDEO_TABLE_FIELDS, SQLVideoWrapper
from saurus.sql.video_parser import VideoFieldQueryParser


def video_mega_search(
    db: PysaurusConnection,
    *,
    include: Sequence[str] = None,
    with_moves: bool = False,
    where: dict = None,
) -> List[dict]:
    parser = VideoFieldQueryParser()
    args = {
        parsed.field: parsed
        for parsed in (parser.parse(key, value) for key, value in (where or {}).items())
    }
    selection = {key: args.pop(key) for key in ("video_id", "filename") if key in args}
    parameters = []
    queries_where = []
    if selection:
        qs = []
        for key, qf in selection.items():
            qs.append(str(qf))
            parameters.extend(qf.values)
        queries_where.append(f"({' OR '.join(qs)})")
    args_keys = list(args.keys())
    queries_where.extend(str(args[key]) for key in args_keys)
    parameters.extend(value for key in args_keys for value in args[key].values)

    query_with = ""
    query_base = (
        f"SELECT {FORMATTED_VIDEO_TABLE_FIELDS}, t.thumbnail AS thumbnail, "
        f"IIF(LENGTH(t.thumbnail), 1, 0) AS with_thumbnails "
        f"FROM video AS v LEFT JOIN video_thumbnail AS t "
        f"ON v.video_id = t.video_id"
    )
    query_with_join = ""
    query_where = ""
    query_with_order = ""

    idx_order = selection["video_id"].values if "video_id" in selection else ()
    if len(idx_order) > 1:
        query_with = (
            f"WITH vid_order(video_id, rank) AS "
            f"(VALUES {','.join(f'({v},{r})' for r, v in enumerate(idx_order))})"
        )
        query_with_join = "LEFT JOIN vid_order AS vo ON v.video_id = vo.video_id"
        query_with_order = "ORDER BY vo.rank"
    if queries_where:
        query_where = f"WHERE {' AND '.join(queries_where)}"
    query = f"""
    {query_with}
    {query_base}
    {query_with_join}
    {query_where}
    {query_with_order}
    """
    videos = [SQLVideoWrapper(row) for row in db.query(query, parameters)]

    video_indices = [video.data["video_id"] for video in videos]
    placeholders = ", ".join(["?"] * len(video_indices))

    errors = defaultdict(list)
    languages = {"a": defaultdict(list), "s": defaultdict(list)}
    properties = defaultdict(dict)
    json_properties = {}
    with_errors = include is None or "errors" in include
    with_audio_languages = include is None or "audio_languages" in include
    with_subtitle_languages = include is None or "subtitle_languages" in include
    with_properties = include is None or "json_properties" in include
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
        prop_types: Dict[int, PropTypeValidator] = {
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
                prop_types[property_id]
                .name: prop_types[property_id]
                .plain_from_strings(values)
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

    if include is None:
        # Return all, use with_moves.
        return [video.json(with_moves) for video in videos]
    else:
        # Use include, ignore with_moves
        fields = include or ("video_id",)
        return [{key: getattr(video, key) for key in fields} for video in videos]
