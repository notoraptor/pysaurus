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
from pysaurus.database.saurus.sql.migration.db_comparison import (
    verify_properties,
    verify_property_enumerations,
    verify_sources,
    verify_video_errors,
    verify_video_languages,
    verify_video_property_values,
    verify_videos,
)
from pysaurus.database.saurus.sql.migration.migrate_json_to_saurus_sql import (
    DB_THUMB_FOLDER,
)
from pysaurus.database.saurus.sql.migration.video_inliner import (
    get_all_fields,
    get_all_getters,
)
from pysaurus.database.saurus.sql.sql_functions import pysaurus_text_to_fts
from pysaurus.database.saurus.sql.pysaurus_connection import PysaurusConnection
from pysaurus.database.saurus.sql.pysaurus_program import PysaurusProgram


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


def verify_video_text(new_db, videos, string_props):
    # Build expected FTS data with pysaurus_text_to_fts transformation
    expected = []
    for video in videos:
        properties = video._get("properties")
        props_text = ";".join(
            v for name in string_props for v in properties.get(name, ())
        )
        expected.append(
            (
                video.video_id,
                pysaurus_text_to_fts(video._get("filename")),
                pysaurus_text_to_fts(video._get("meta_title")),
                pysaurus_text_to_fts(props_text) if props_text else None,
            )
        )
    expected.sort()
    rows = new_db.query_all(
        "SELECT rowid, filename, meta_title, properties FROM video_text ORDER BY rowid"
    )
    actual = [
        (row["rowid"], row["filename"], row["meta_title"], row["properties"])
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
