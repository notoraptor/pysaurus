"""To SQL."""

from pysaurus.core.components import AbsolutePath
from pysaurus.core.json_backup import JsonBackup
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database.db_settings import DbSettings
from pysaurus.database.db_way_def import DbWays
from pysaurus.properties.properties import PropType
from pysaurus.updates.video_inliner import (
    get_all_fields,
    get_all_getters,
    get_video_text,
)
from pysaurus.video import Video
from saurus.sql.pysaurus_database import PysaurusDatabase
from saurus.sql.pysaurus_program import PysaurusProgram


def format_prop_val(values, typ):
    return ((int(v) if typ is bool else v) for v in values)


def export_db_to_sql(db_name: str, db_path: AbsolutePath, notifier):
    ways = DbWays(db_path)

    # Clean thumb folder if empty
    thumb_folder = ways.db_thumb_folder
    if thumb_folder.isdir():
        if not thumb_folder.listdir():
            print(f"[{db_name}] Thumb folder is empty, deleting")
            thumb_folder.delete()
            assert not thumb_folder.exists()

    # Delete previous SQL file if existing
    sql_path = ways.db_sql_path
    if sql_path.exists():
        sql_path.delete()
        print(f"[{db_name}] Deleted old sql path")
    assert not sql_path.exists()
    new_db = PysaurusDatabase(sql_path.path)
    assert sql_path.isfile()

    # Load database JSON
    json_backup = JsonBackup(ways.db_json_path, notifier)
    json_dict = json_backup.load()
    assert isinstance(json_dict, dict)

    # Format data for SQL tables
    with Profiler(f"[{db_name}] Get and format data", notifier):
        version = json_dict.get("version", -1)
        settings = DbSettings(json_dict.get("settings", {}))
        date = json_dict.get("date")
        sources = [AbsolutePath(path) for path in json_dict.get("folders", ())]
        source_tree = PathTree(sources)

        def get_discarded(idx, vd: Video, fd):
            return not source_tree.in_folders(vd.filename)

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
            (video_id, get_video_text(video, string_props))
            for video_id, video in enumerate(videos)
        ]

    # Save data into SQL table
    with Profiler(f"[{db_name}] Insert into SQL database", notifier):
        new_db.modify(
            "INSERT INTO collection ("
            "collection_id, "
            "name, "
            "version, "
            "date_updated, "
            "miniature_pixel_distance_radius, "
            "miniature_group_min_size) "
            "VALUES(?,?,?,?,?,?)",
            [
                0,
                db_name,
                version,
                date,
                settings.miniature_pixel_distance_radius,
                settings.miniature_group_min_size,
            ],
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
            "INSERT INTO video_text (video_id, content) VALUES(?, ?)",
            video_texts,
            many=True,
        )


def main(notifier):
    application = PysaurusProgram()
    db_name_to_path = {path.title: path for path in application.get_database_paths()}
    for db_name in sorted(db_name_to_path):
        with Profiler(f"[{db_name}] export", notifier):
            export_db_to_sql(db_name, db_name_to_path[db_name], notifier)


if __name__ == "__main__":
    with Profiler("main", DEFAULT_NOTIFIER):
        main(DEFAULT_NOTIFIER)
