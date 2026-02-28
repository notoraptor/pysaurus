"""Shared comparison functions for JSON vs SQL database verification."""


def format_prop_val(values, typ):
    return ((int(v) if typ is bool else v) for v in values)


def _enum_to_str(value, typ):
    if typ is bool:
        return str(int(value))
    return str(value)


def _diff_sets(actual_set, expected_set, label):
    only_sql = actual_set - expected_set
    only_json = expected_set - actual_set
    lines = []
    if only_sql:
        lines.append(f"  only in SQL ({len(only_sql)}):")
        for item in sorted(only_sql, key=repr)[:10]:
            lines.append(f"    {item!r}")
        if len(only_sql) > 10:
            lines.append(f"    ... ({len(only_sql)} total)")
    if only_json:
        lines.append(f"  only in JSON ({len(only_json)}):")
        for item in sorted(only_json, key=repr)[:10]:
            lines.append(f"    {item!r}")
        if len(only_json) > 10:
            lines.append(f"    ... ({len(only_json)} total)")
    assert not lines, f"{label}:\n" + "\n".join(lines)


def verify_sources(new_db, sources):
    rows = new_db.query_all("SELECT source FROM collection_source")
    sql_sources = {row["source"] for row in rows}
    json_sources = {s.path for s in sources}
    _diff_sets(sql_sources, json_sources, "sources")


def verify_videos(
    new_db,
    videos,
    video_fields,
    video_field_getter,
    exclude_fields=(),
    match_field="video_id",
):
    fields_to_check = [
        f for f in video_fields if f not in exclude_fields and f != match_field
    ]
    fields_str = ",".join(video_fields)
    rows = new_db.query_all(f"SELECT {fields_str} FROM video ORDER BY video_id")
    sql_keys = {row[match_field] for row in rows}
    json_keys = {video_field_getter[match_field](None, v, match_field) for v in videos}
    _diff_sets(sql_keys, json_keys, f"video {match_field}s")
    sql_by_key = {row[match_field]: row for row in rows}
    diffs = []
    for video in videos:
        key = video_field_getter[match_field](None, video, match_field)
        if key not in sql_by_key:
            continue
        row = sql_by_key[key]
        for field in fields_to_check:
            expected = video_field_getter[field](None, video, field)
            actual = row[field]
            if isinstance(expected, bool):
                expected = int(expected)
            if actual != expected:
                diffs.append(f"  [{key}] {field}: SQL {actual!r} != JSON {expected!r}")
    assert not diffs, (
        f"video field diffs ({len(diffs)}):\n"
        + "\n".join(diffs[:20])
        + (f"\n  ... ({len(diffs)} total)" if len(diffs) > 20 else "")
    )


def verify_video_errors(new_db, videos, vid_map=None):
    expected = {
        (_map_vid(vid_map, video.video_id), error)
        for video in videos
        for error in video._get("errors")
    }
    rows = new_db.query_all(
        "SELECT video_id, error FROM video_error ORDER BY video_id, error"
    )
    actual = {(row["video_id"], row["error"]) for row in rows}
    _diff_sets(actual, expected, "video_error")


def verify_video_languages(new_db, videos, vid_map=None):
    expected = set()
    for video in videos:
        mapped_id = _map_vid(vid_map, video.video_id)
        for r, lang_code in enumerate(video._get("audio_languages")):
            expected.add((mapped_id, "a", lang_code, r))
        for r, lang_code in enumerate(video._get("subtitle_languages")):
            expected.add((mapped_id, "s", lang_code, r))
    rows = new_db.query_all(
        "SELECT video_id, stream, lang_code, rank "
        "FROM video_language ORDER BY video_id, stream, rank"
    )
    actual = {
        (row["video_id"], row["stream"], row["lang_code"], row["rank"]) for row in rows
    }
    _diff_sets(actual, expected, "video_language")


def verify_properties(new_db, prop_types):
    expected = {
        (i, pt.name, pt.type.__name__, pt.multiple) for i, pt in enumerate(prop_types)
    }
    rows = new_db.query_all(
        "SELECT property_id, name, type, multiple FROM property ORDER BY property_id"
    )
    actual = {
        (row["property_id"], row["name"], row["type"], row["multiple"]) for row in rows
    }
    _diff_sets(actual, expected, "property")


def verify_property_enumerations(new_db, prop_types):
    expected = {
        (i, _enum_to_str(e, pt.type), r)
        for i, pt in enumerate(prop_types)
        for r, e in enumerate(pt.enumeration or [pt.default])
    }
    rows = new_db.query_all(
        "SELECT property_id, enum_value, rank "
        "FROM property_enumeration ORDER BY property_id, rank"
    )
    actual = {(row["property_id"], row["enum_value"], row["rank"]) for row in rows}
    _diff_sets(actual, expected, "property_enumeration")


def verify_video_property_values(
    new_db, videos, pt_name_to_pid, pt_name_to_type, vid_map=None
):
    expected = {
        (_map_vid(vid_map, video.video_id), pt_name_to_pid[name], str(property_value))
        for video in videos
        for name, values in video._get("properties").items()
        for property_value in format_prop_val(values, pt_name_to_type[name])
    }
    rows = new_db.query_all(
        "SELECT video_id, property_id, property_value "
        "FROM video_property_value ORDER BY video_id, property_id, property_value"
    )
    actual = {
        (row["video_id"], row["property_id"], row["property_value"]) for row in rows
    }
    _diff_sets(actual, expected, "video_property_value")


def _map_vid(vid_map, video_id):
    if vid_map is None:
        return video_id
    return vid_map[video_id]
