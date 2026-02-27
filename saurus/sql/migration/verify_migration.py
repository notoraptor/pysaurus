"""Verify JSON to SQL migration."""

import sys

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.json_backup import JsonBackup
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database.db_way_def import DbWays
from pysaurus.database.jsdb.jsdb_prop_type import PropType
from pysaurus.database.jsdb.jsdbvideo.lazy_video import LazyVideo as Video
from pysaurus.database.jsdb.thubmnail_database.thumbnail_manager import ThumbnailManager
from saurus.sql.migration.migrate_json_to_saurus_sql import (
    DB_THUMB_FOLDER,
    format_prop_val,
)
from saurus.sql.migration.video_inliner import (
    get_all_fields,
    get_all_getters,
    get_video_text_triple,
)
from saurus.sql.pysaurus_connection import PysaurusConnection
from saurus.sql.pysaurus_program import PysaurusProgram


def main(notifier):
    if len(sys.argv) > 1:
        home_dir = AbsolutePath(sys.argv[1])
    else:
        home_dir = None
    application = PysaurusProgram(home_dir=home_dir)
    failures = []
    for db_path in sorted(application.get_database_paths()):
        db_name = db_path.title
        try:
            with Profiler(f"[{db_name}] verify", notifier):
                verify_db(db_path, notifier)
            print(f"[{db_name}] OK", file=sys.stderr)
        except Exception as e:
            print(f"[{db_name}] FAILED: {e}", file=sys.stderr)
            failures.append(db_name)
    if failures:
        print(f"FAILED databases: {failures}", file=sys.stderr)
        sys.exit(1)


def verify_db(db_path: AbsolutePath, notifier):
    db_name = db_path.title
    ways = DbWays(db_path)
    ways.define(DB_THUMB_FOLDER, is_folder=True, create_folder=False)

    # Load JSON data
    json_dict = JsonBackup(ways.db_json_path, notifier).load()
    if not isinstance(json_dict, dict):
        raise TypeError(f"Expected dict from JSON, got {type(json_dict).__name__}")

    version = json_dict.get("version", -1)
    date = json_dict.get("date")
    sources = [AbsolutePath(path) for path in json_dict.get("folders", ())]
    source_tree = PathTree(sources)

    def get_discarded(local_video_id, local_video: Video, local_field):
        return not source_tree.in_folders(local_video.filename)

    video_field_getter = get_all_getters()
    video_field_getter["discarded"] = get_discarded
    video_fields = get_all_fields()

    videos = [Video(None, video_dict) for video_dict in json_dict.get("videos", ())]
    prop_types = sorted(
        (PropType.from_dict(d) for d in json_dict.get("prop_types", ())),
        key=lambda p: p.name,
    )
    pt_name_to_pid = {pt.name: i for i, pt in enumerate(prop_types)}
    pt_name_to_type = {pt.name: pt.type for pt in prop_types}
    string_props = [pt.name for pt in prop_types if pt.type is str]

    # Open SQL database
    sql_path = ways.db_sql_path
    if not sql_path.isfile():
        raise FileNotFoundError(f"SQL database not found: {sql_path}")
    new_db = PysaurusConnection(sql_path.path)

    verify_collection(new_db, db_name, version, date)
    verify_sources(new_db, sources)
    verify_videos(new_db, videos, video_fields, video_field_getter)
    verify_video_errors(new_db, videos)
    verify_video_languages(new_db, videos)
    verify_properties(new_db, prop_types)
    verify_property_enumerations(new_db, prop_types)
    verify_video_property_values(new_db, videos, pt_name_to_pid, pt_name_to_type)
    verify_video_text(new_db, videos, string_props)
    verify_video_thumbnails(new_db, videos, ways)


def verify_collection(new_db, db_name, version, date):
    rows = new_db.query_all("SELECT name, version, date_updated FROM collection")
    assert len(rows) == 1, f"Expected 1 collection row, got {len(rows)}"
    row = rows[0]
    assert row["name"] == db_name, f"name: {row['name']!r} != {db_name!r}"
    assert row["version"] == version, f"version: {row['version']!r} != {version!r}"
    assert row["date_updated"] == date, f"date: {row['date_updated']!r} != {date!r}"


def verify_sources(new_db, sources):
    rows = new_db.query_all("SELECT source FROM collection_source")
    sql_sources = {row["source"] for row in rows}
    json_sources = {s.path for s in sources}
    assert sql_sources == json_sources, f"sources differ: {sql_sources ^ json_sources}"


def verify_videos(new_db, videos, video_fields, video_field_getter):
    fields_str = ",".join(video_fields)
    rows = new_db.query_all(f"SELECT {fields_str} FROM video ORDER BY video_id")
    assert len(rows) == len(videos), (
        f"video count: SQL {len(rows)} != JSON {len(videos)}"
    )
    sql_by_id = {row["video_id"]: row for row in rows}
    for video in videos:
        vid = video.video_id
        assert vid in sql_by_id, f"video_id {vid} not found in SQL"
        row = sql_by_id[vid]
        for field in video_fields:
            expected = video_field_getter[field](None, video, field)
            actual = row[field]
            if isinstance(expected, bool):
                expected = int(expected)
            assert actual == expected, (
                f"video[{vid}].{field}: SQL {actual!r} != JSON {expected!r}"
            )


def verify_video_errors(new_db, videos):
    expected = sorted(
        (video.video_id, error) for video in videos for error in video._get("errors")
    )
    rows = new_db.query_all(
        "SELECT video_id, error FROM video_error ORDER BY video_id, error"
    )
    actual = [(row["video_id"], row["error"]) for row in rows]
    assert len(actual) == len(expected), (
        f"video_error count: SQL {len(actual)} != JSON {len(expected)}"
    )
    for i, (a, e) in enumerate(zip(actual, expected)):
        assert a == e, f"video_error[{i}]: SQL {a!r} != JSON {e!r}"


def verify_video_languages(new_db, videos):
    expected = []
    for video in videos:
        for r, lang_code in enumerate(video._get("audio_languages")):
            expected.append((video.video_id, "a", lang_code, r))
        for r, lang_code in enumerate(video._get("subtitle_languages")):
            expected.append((video.video_id, "s", lang_code, r))
    expected.sort(key=lambda t: (t[0], t[1], t[3]))
    rows = new_db.query_all(
        "SELECT video_id, stream, lang_code, rank "
        "FROM video_language ORDER BY video_id, stream, rank"
    )
    actual = [
        (row["video_id"], row["stream"], row["lang_code"], row["rank"]) for row in rows
    ]
    assert len(actual) == len(expected), (
        f"video_language count: SQL {len(actual)} != JSON {len(expected)}"
    )
    for i, (a, e) in enumerate(zip(actual, expected)):
        assert a == e, f"video_language[{i}]: SQL {a!r} != JSON {e!r}"


def verify_properties(new_db, prop_types):
    expected = [
        (i, pt.name, pt.type.__name__, pt.multiple) for i, pt in enumerate(prop_types)
    ]
    rows = new_db.query_all(
        "SELECT property_id, name, type, multiple FROM property ORDER BY property_id"
    )
    actual = [
        (row["property_id"], row["name"], row["type"], row["multiple"]) for row in rows
    ]
    assert len(actual) == len(expected), (
        f"property count: SQL {len(actual)} != JSON {len(expected)}"
    )
    for i, (a, e) in enumerate(zip(actual, expected)):
        assert a == e, f"property[{i}]: SQL {a!r} != JSON {e!r}"


def _enum_to_str(value, typ):
    if typ is bool:
        return str(int(value))
    return str(value)


def verify_property_enumerations(new_db, prop_types):
    expected = [
        (i, _enum_to_str(e, pt.type), r)
        for i, pt in enumerate(prop_types)
        for r, e in enumerate(pt.enumeration or [pt.default])
    ]
    rows = new_db.query_all(
        "SELECT property_id, enum_value, rank "
        "FROM property_enumeration ORDER BY property_id, rank"
    )
    actual = [(row["property_id"], row["enum_value"], row["rank"]) for row in rows]
    assert len(actual) == len(expected), (
        f"property_enumeration count: SQL {len(actual)} != JSON {len(expected)}"
    )
    for i, (a, e) in enumerate(zip(actual, expected)):
        assert a == e, f"property_enumeration[{i}]: SQL {a!r} != JSON {e!r}"


def verify_video_property_values(new_db, videos, pt_name_to_pid, pt_name_to_type):
    expected = [
        (video.video_id, pt_name_to_pid[name], str(property_value))
        for video in videos
        for name, values in sorted(video._get("properties").items(), key=lambda c: c[0])
        for property_value in format_prop_val(values, pt_name_to_type[name])
    ]
    expected.sort()
    rows = new_db.query_all(
        "SELECT video_id, property_id, property_value "
        "FROM video_property_value ORDER BY video_id, property_id, property_value"
    )
    actual = [
        (row["video_id"], row["property_id"], row["property_value"]) for row in rows
    ]
    assert len(actual) == len(expected), (
        f"video_property_value count: SQL {len(actual)} != JSON {len(expected)}"
    )
    for i, (a, e) in enumerate(zip(actual, expected)):
        assert a == e, f"video_property_value[{i}]: SQL {a!r} != JSON {e!r}"


def verify_video_text(new_db, videos, string_props):
    expected = [
        (video.video_id, *get_video_text_triple(video, string_props))
        for video in videos
    ]
    expected.sort()
    rows = new_db.query_all(
        "SELECT video_id, filename, meta_title, properties "
        "FROM video_text ORDER BY video_id"
    )
    actual = [
        (row["video_id"], row["filename"], row["meta_title"], row["properties"] or "")
        for row in rows
    ]
    assert len(actual) == len(expected), (
        f"video_text count: SQL {len(actual)} != JSON {len(expected)}"
    )
    for i, (a, e) in enumerate(zip(actual, expected)):
        assert a == e, f"video_text[{i}]: SQL {a!r} != JSON {e!r}"


def verify_video_thumbnails(new_db, videos, ways):
    video_filename_to_id = {video.filename.path: video.video_id for video in videos}
    thumb_sql_path = ways.db_thumb_sql_path
    if not thumb_sql_path.isfile():
        raise FileNotFoundError(f"Thumbnail database not found: {thumb_sql_path}")
    thm = ThumbnailManager(thumb_sql_path)
    with thm.thumb_db:
        expected_count = sum(
            1
            for row in thm.thumb_db.query("SELECT filename FROM video_to_thumbnail")
            if row["filename"] in video_filename_to_id
        )
    rows = new_db.query_all("SELECT video_id FROM video_thumbnail")
    actual_count = len(rows)
    assert actual_count == expected_count, (
        f"video_thumbnail count: SQL {actual_count} != thumb_db {expected_count}"
    )


if __name__ == "__main__":
    with Profiler("verify", DEFAULT_NOTIFIER):
        main(DEFAULT_NOTIFIER)
