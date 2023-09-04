from typing import List

from pysaurus.video.lazy_video import LazyVideo as Video


def get_zero(i, video, key):
    return 0


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
    "discarded",
    "date_entry_modified",
    "date_entry_opened",
    "similarity_id",
]
VIDEO_FIELDS_NO_VIDEO_ID = VIDEO_FIELDS[1:]
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
    "discarded": get_zero,
    "date_entry_modified": get_default,
    "date_entry_opened": get_default,
    "similarity_id": get_default,
}


def get_all_fields():
    return VIDEO_FIELDS.copy()


def get_all_getters():
    return VIDEO_FIELD_GETTER.copy()


def get_flatten_fields():
    return VIDEO_FIELDS_NO_VIDEO_ID


def flatten_video(video: Video):
    return [
        VIDEO_FIELD_GETTER[field](None, video, field)
        for field in VIDEO_FIELDS_NO_VIDEO_ID
    ]


def get_video_text(video: Video, prop_names: List[str]):
    properties = video._get("properties")
    return (
        f"{video._get('filename')};{video._get('meta_title')};"
        f"{';'.join(v for name in prop_names for v in properties.get(name, ()))}"
    )
