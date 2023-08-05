"""To SQL."""
from typing import List

from pysaurus.core.components import AbsolutePath
from pysaurus.core.json_backup import JsonBackup
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler
from pysaurus.database.db_settings import DbSettings
from pysaurus.database.db_way_def import DbWays
from pysaurus.properties.properties import PropType
from pysaurus.video import Video
from saurus.sql.pysaurus_collection import PysaurusDatabase
from saurus.sql.pysaurus_program import PysaurusProgram


def format_prop_val(values, typ):
    return ((int(v) if typ is bool else v) for v in values)


def get_video_text(video: Video, prop_names: List[str]):
    properties = video._get("properties")
    return (
        f"{video._get('filename')};{video._get('meta_title')};"
        f"{';'.join(v for name in prop_names for v in properties.get(name, ()))}"
    )


def get_none(i, video, key):
    return None


def get_i(i, video, key):
    return i


def get_default(i, video: Video, key):
    return video._get(key)


def get_field(i, video: Video, key):
    return getattr(video, key)


def get_runtime(i, video: Video, key):
    return video.runtime._get(key)


VIDEO_FIELDS = [
    "video_id",
    "filename",
    "file_size",
    "unreadable",
    "audio_bit_rate",
    "audio_bits",
    "audio_codec",
    "audio_codec_description",
    "bit_depth",
    "channels",
    "container_format",
    "device_name",
    "duration",
    "duration_time_base",
    "frame_rate_den",
    "frame_rate_num",
    "height",
    "meta_title",
    "sample_rate",
    "video_codec",
    "video_codec_description",
    "width",
    "mtime",
    "driver_id",
    "is_file",
    "date_entry_modified",
    "date_entry_opened",
    "similarity_id",
]
VIDEO_FIELD_GETTER = {
    "video_id": get_i,
    "filename": get_default,
    "file_size": get_default,
    "unreadable": get_default,
    "audio_bit_rate": get_default,
    "audio_bits": get_default,
    "audio_codec": get_default,
    "audio_codec_description": get_default,
    "bit_depth": get_default,
    "channels": get_default,
    "container_format": get_default,
    "device_name": get_default,
    "duration": get_field,
    "duration_time_base": get_field,
    "frame_rate_den": get_field,
    "frame_rate_num": get_default,
    "height": get_default,
    "meta_title": get_default,
    "sample_rate": get_default,
    "video_codec": get_default,
    "video_codec_description": get_default,
    "width": get_default,
    "mtime": get_runtime,
    "driver_id": get_runtime,
    "is_file": get_runtime,
    "date_entry_modified": get_default,
    "date_entry_opened": get_default,
    "similarity_id": get_default,
}


def main(notifier):
    tested_db_name = "adult videos"

    application = PysaurusProgram()
    db_name_to_path = {path.title: path for path in application.get_database_paths()}
    assert tested_db_name in db_name_to_path, db_name_to_path.keys()
    for db_name in sorted(db_name_to_path):
        print(db_name)
    ways = DbWays(db_name_to_path[tested_db_name])
    for name, path in ways:
        print(name, path)
    sql_path = ways.db_sql_path
    if sql_path.exists():
        sql_path.delete()
        print("Deleting old sql path")
    assert not sql_path.exists()
    new_db = PysaurusDatabase(sql_path.path)
    assert sql_path.isfile()

    json_backup = JsonBackup(ways.db_json_path, notifier)
    json_dict = json_backup.load()
    assert isinstance(json_dict, dict)

    version = json_dict.get("version", -1)
    settings = DbSettings(json_dict.get("settings", {}))
    date = json_dict.get("date")
    sources = [AbsolutePath(path) for path in json_dict.get("folders", ())]
    with Profiler("Get videos", notifier):
        videos = sorted(
            Video(None, video_dict) for video_dict in json_dict.get("videos", ())
        )
    with Profiler(f"Get video lines ({len(videos)} videos)", notifier):
        video_lines = [
            [VIDEO_FIELD_GETTER[field](i, video, field) for field in VIDEO_FIELDS]
            for i, video in enumerate(videos)
        ]
    with Profiler("Get video errors", notifier):
        video_errors = [
            (i, error)
            for i, video in enumerate(videos)
            for error in sorted(video._get("errors"))
        ]
    with Profiler("Get video languages", notifier):
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
    with Profiler("Get property types and values", notifier):
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
    with Profiler("Get video texts", notifier):
        video_texts = [
            (video_id, get_video_text(video, string_props))
            for video_id, video in enumerate(videos)
        ]

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
            tested_db_name,
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
    with Profiler("Insert videos", notifier):
        new_db.modify(
            f"INSERT INTO video "
            f"({','.join(VIDEO_FIELDS)}) "
            f"VALUES ({','.join('?' for _ in VIDEO_FIELDS)})",
            video_lines,
            many=True,
        )
    with Profiler("Insert video errors", notifier):
        new_db.modify(
            "INSERT INTO video_error (video_id, error) VALUES (?, ?)",
            video_errors,
            many=True,
        )
    with Profiler("Insert video languages", notifier):
        new_db.modify(
            "INSERT INTO video_language (video_id, stream, lang_code, rank) "
            "VALUES (?, ?, ?, ?)",
            video_audio_languages + video_subtitle_languages,
            many=True,
        )
    with Profiler("Insert prop types", notifier):
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
    with Profiler("Insert video property values", notifier):
        new_db.modify(
            "INSERT INTO video_property_value (video_id, property_id, property_value) "
            "VALUES (?, ?, ?)",
            video_property_values,
            many=True,
        )
    with Profiler("Insert video texts", notifier):
        new_db.modify(
            "INSERT INTO video_text (video_id, content) VALUES(?, ?)",
            video_texts,
            many=True,
        )


if __name__ == "__main__":
    with Profiler("main", DEFAULT_NOTIFIER):
        main(DEFAULT_NOTIFIER)
