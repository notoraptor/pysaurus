"""Compare JSON and SQL databases to detect divergences."""

import argparse
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
from pysaurus.database.saurus.sql.migration.video_inliner import (
    get_all_fields,
    get_all_getters,
)
from pysaurus.database.saurus.sql.pysaurus_connection import PysaurusConnection
from pysaurus.database.saurus.sql.pysaurus_program import PysaurusProgram

EXCLUDE_FIELDS = {"date_entry_modified", "date_entry_opened", "video_id"}


def main(notifier):
    parser = argparse.ArgumentParser(description="Compare JSON and SQL databases.")
    parser.add_argument("--home", help="home directory")
    parser.add_argument("--db", help="database name to compare (default: all)")
    args = parser.parse_args()
    home_dir = AbsolutePath(args.home) if args.home else None
    application = PysaurusProgram(home_dir=home_dir)
    failures = []
    for db_path in sorted(application.get_database_paths()):
        db_name = db_path.title
        if args.db is not None and db_name != args.db:
            continue
        try:
            with Profiler(f"[{db_name}] compare", notifier):
                compare_db(db_path, notifier)
            print(f"[{db_name}] OK", file=sys.stderr)
        except Exception as e:
            print(f"[{db_name}] FAILED: {e}", file=sys.stderr)
            failures.append(db_name)
    if failures:
        print(f"FAILED databases: {failures}", file=sys.stderr)
        sys.exit(1)


def compare_db(db_path: AbsolutePath, notifier):
    ways = DbWays(db_path)

    # Load JSON data
    json_dict = JsonBackup(ways.db_json_path, notifier).load()
    if not isinstance(json_dict, dict):
        raise TypeError(f"Expected dict from JSON, got {type(json_dict).__name__}")

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

    # Open SQL database
    sql_path = ways.db_sql_path
    if not sql_path.isfile():
        raise FileNotFoundError(f"SQL database not found: {sql_path}")
    sql_db = PysaurusConnection(sql_path.path)

    # Build JSON video_id -> SQL video_id mapping via filename
    sql_filename_to_id = {
        row["filename"]: row["video_id"]
        for row in sql_db.query_all("SELECT video_id, filename FROM video")
    }
    vid_map = {}
    for video in videos:
        sql_vid = sql_filename_to_id.get(video.filename.path)
        if sql_vid is not None:
            vid_map[video.video_id] = sql_vid

    verify_sources(sql_db, sources)
    verify_videos(
        sql_db,
        videos,
        video_fields,
        video_field_getter,
        exclude_fields=EXCLUDE_FIELDS,
        match_field="filename",
    )
    verify_video_errors(sql_db, videos, vid_map=vid_map)
    verify_video_languages(sql_db, videos, vid_map=vid_map)
    verify_properties(sql_db, prop_types)
    verify_property_enumerations(sql_db, prop_types)
    verify_video_property_values(
        sql_db, videos, pt_name_to_pid, pt_name_to_type, vid_map=vid_map
    )
    verify_video_thumbnails(sql_db, videos, ways, vid_map=vid_map)


def verify_video_thumbnails(sql_db, videos, ways, vid_map=None):
    video_filename_to_json_id = {
        video.filename.path: video.video_id for video in videos
    }
    thumb_sql_path = ways.db_thumb_sql_path
    if not thumb_sql_path.isfile():
        raise FileNotFoundError(f"Thumbnail database not found: {thumb_sql_path}")
    thm = ThumbnailManager(thumb_sql_path)
    with thm.thumb_db:
        json_thumb_filenames = {
            row["filename"]
            for row in thm.thumb_db.query("SELECT filename FROM video_to_thumbnail")
            if row["filename"] in video_filename_to_json_id
        }
    rows = sql_db.query_all(
        "SELECT v.filename FROM video_thumbnail vt "
        "JOIN video v ON v.video_id = vt.video_id"
    )
    sql_thumb_filenames = {row["filename"] for row in rows}
    only_sql = sql_thumb_filenames - json_thumb_filenames
    only_json = json_thumb_filenames - sql_thumb_filenames
    lines = []
    if only_sql:
        lines.append(f"  only in SQL ({len(only_sql)}):")
        for f in sorted(only_sql)[:10]:
            lines.append(f"    {f}")
        if len(only_sql) > 10:
            lines.append(f"    ... ({len(only_sql)} total)")
    if only_json:
        lines.append(f"  only in JSON ({len(only_json)}):")
        for f in sorted(only_json)[:10]:
            lines.append(f"    {f}")
        if len(only_json) > 10:
            lines.append(f"    ... ({len(only_json)} total)")
    assert not lines, "video_thumbnail:\n" + "\n".join(lines)


if __name__ == "__main__":
    with Profiler("compare", DEFAULT_NOTIFIER):
        main(DEFAULT_NOTIFIER)
