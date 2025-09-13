"""To SQL."""

import sys

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.file_size import FileSize
from pysaurus.core.json_backup import JsonBackup
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database.db_way_def import DbWays
from pysaurus.database.jsdb.jsdb_prop_type import PropType
from pysaurus.database.jsdb.jsdbvideo.lazy_video import LazyVideo as Video
from pysaurus.database.jsdb.thubmnail_database.thumbnail_manager import ThumbnailManager
from pysaurus.updates.video_inliner import (
    get_all_fields,
    get_all_getters,
    get_video_text_triple,
)
from saurus.sql.pysaurus_connection import PysaurusConnection
from saurus.sql.pysaurus_program import PysaurusProgram

DB_THUMB_FOLDER = ("thumb_folder", "thumbnails")


def main(notifier):
    application = PysaurusProgram()
    for db_path in sorted(application.get_database_paths()):
        db_name = db_path.title
        # if db_name not in ("example_db_in_pysaurus", "Divertissement"):
        #     continue
        with Profiler(f"[{db_name}] export", notifier):
            export_db_to_sql(db_path, notifier)


def export_db_to_sql(db_path: AbsolutePath, notifier):
    db_name = db_path.title
    ways = DbWays(db_path)
    ways.define(DB_THUMB_FOLDER, is_folder=True, create_folder=False)

    # Clean thumb folder if empty
    thumb_folder = ways.get(DB_THUMB_FOLDER)
    if thumb_folder.isdir():
        if not thumb_folder.listdir():
            print(f"[{db_name}] Thumb folder is empty, deleting", file=sys.stderr)
            thumb_folder.delete()
            assert not thumb_folder.exists()

    # Delete previous SQL file if existing
    sql_path = ways.db_sql_path
    if sql_path.exists():
        prev_size = FileSize(sql_path.get_size())
        sql_path.delete()
        print(f"[{db_name}] Deleted old sql path ({prev_size})", file=sys.stderr)
    assert not sql_path.exists()
    new_db = PysaurusConnection(sql_path.path)
    assert sql_path.isfile()

    # Load database JSON
    json_backup = JsonBackup(ways.db_json_path, notifier)
    json_dict = json_backup.load()
    assert isinstance(json_dict, dict)

    # Format data for SQL tables
    with Profiler(f"[{db_name}] Get and format data", notifier):
        version = json_dict.get("version", -1)
        date = json_dict.get("date")
        sources = [AbsolutePath(path) for path in json_dict.get("folders", ())]
        source_tree = PathTree(sources)

        def get_discarded(local_video_id, local_video: Video, local_field):
            return not source_tree.in_folders(local_video.filename)

        video_field_getter = get_all_getters()
        video_field_getter["discarded"] = get_discarded
        video_fields = get_all_fields()

        videos = sorted(
            Video(None, video_dict) for video_dict in json_dict.get("videos", ())
        )
        video_lines = [
            [video_field_getter[field](i, video, field) for field in video_fields]
            for i, video in enumerate(videos)
        ]
        video_errors = [
            (i, error)
            for i, video in enumerate(videos)
            for error in sorted(video._get("errors"))
        ]
        video_audio_languages = [
            (i, "a", lang_code, r)
            for i, video in enumerate(videos)
            for r, lang_code in enumerate(video._get("audio_languages"))
        ]
        video_subtitle_languages = [
            (i, "s", lang_code, r)
            for i, video in enumerate(videos)
            for r, lang_code in enumerate(video._get("subtitle_languages"))
        ]
        prop_types = sorted(
            (
                PropType.from_dict(prop_dict)
                for prop_dict in json_dict.get("prop_types", ())
            ),
            key=lambda p: p.name,
        )
        pt_name_to_pid = {pt.name: i for i, pt in enumerate(prop_types)}
        pt_name_to_type = {pt.name: pt.type for pt in prop_types}
        string_props = [pt.name for pt in prop_types if pt.type is str]
        prop_lines = [
            (i, pt.name, pt.type.__name__, pt.multiple)
            for i, pt in enumerate(prop_types)
        ]
        prop_enums = [
            (i, e, r)
            for i, pt in enumerate(prop_types)
            for r, e in enumerate(pt.enumeration or [pt.default])
        ]
        video_property_values = [
            (video_id, pt_name_to_pid[name], property_value)
            for video_id, video in enumerate(videos)
            for name, values in sorted(
                video._get("properties").items(), key=lambda c: c[0]
            )
            for property_value in format_prop_val(values, pt_name_to_type[name])
        ]
        video_texts = [
            (video_id, *get_video_text_triple(video, string_props))
            for video_id, video in enumerate(videos)
        ]

    # Save data into SQL table
    with Profiler(f"[{db_name}] Insert into SQL database", notifier):
        new_db.modify(
            "INSERT INTO collection ("
            "collection_id, "
            "name, "
            "version, "
            "date_updated) "
            "VALUES(?,?,?,?)",
            [0, db_name, version, date],
        )
        new_db.modify(
            "INSERT INTO collection_source (source) VALUES(?)",
            [(path.path,) for path in sources],
            many=True,
        )
        new_db.modify(
            f"INSERT INTO video "
            f"({','.join(video_fields)}) "
            f"VALUES ({','.join('?' for _ in video_fields)})",
            video_lines,
            many=True,
        )
        new_db.modify(
            "INSERT INTO video_error (video_id, error) VALUES (?, ?)",
            video_errors,
            many=True,
        )
        new_db.modify(
            "INSERT INTO video_language (video_id, stream, lang_code, rank) "
            "VALUES (?, ?, ?, ?)",
            video_audio_languages + video_subtitle_languages,
            many=True,
        )
        new_db.modify(
            "INSERT INTO property (property_id, name, type, multiple) "
            "VALUES (?, ?, ?, ?)",
            prop_lines,
            many=True,
        )
        new_db.modify(
            "INSERT INTO property_enumeration (property_id, enum_value, rank) "
            "VALUES (?, ?, ?)",
            prop_enums,
            many=True,
        )
        new_db.modify(
            "INSERT INTO video_property_value (video_id, property_id, property_value) "
            "VALUES (?, ?, ?)",
            video_property_values,
            many=True,
        )
        new_db.modify(
            "INSERT INTO video_text "
            "(video_id, filename, meta_title, properties) VALUES(?, ?, ?, ?)",
            video_texts,
            many=True,
        )

    # Move thumbnails into new SQL database
    with Profiler(f"[{db_name}] Move thumbnails", notifier):
        video_filename_to_id = {
            video.filename.path: i for i, video in enumerate(videos)
        }
        thumb_sql_path = ways.db_thumb_sql_path
        assert thumb_sql_path.isfile()
        thm = ThumbnailManager(ways.db_thumb_sql_path)
        with Profiler(f"[{db_name}] read thumbnails", notifier):
            thumbs = [
                (video_filename_to_id[row["filename"]], row["thumbnail"])
                for row in thm.thumb_db.query(
                    "SELECT filename, thumbnail FROM video_to_thumbnail"
                )
                if row["filename"] in video_filename_to_id
            ]
        with Profiler(f"[{db_name}]write {len(thumbs)} thumbnails", notifier):
            new_db.modify(
                "INSERT INTO video_thumbnail (video_id, thumbnail) VALUES(?, ?)",
                thumbs,
                many=True,
            )

    print(f"[{db_name}] Finished, {FileSize(sql_path.get_size())}", file=sys.stderr)


def format_prop_val(values, typ):
    return ((int(v) if typ is bool else v) for v in values)


if __name__ == "__main__":
    with Profiler("main", DEFAULT_NOTIFIER):
        main(DEFAULT_NOTIFIER)
