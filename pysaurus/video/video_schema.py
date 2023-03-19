from pysaurus.core.jsonable import Type
from pysaurus.core.schematizable import Schema, SchemaType
from pysaurus.video.lazy_video_runtime_info import LazyVideoRuntimeInfo


class VideoSchema(Schema):
    __slots__ = ()

    def __init__(self):
        super().__init__(
            [
                Type("filename", ("f", str), None),
                Type("file_size", "s", 0),
                Type("errors", "e", list()),
                Type("video_id", ("j", int), None),
                SchemaType("runtime", ("R", LazyVideoRuntimeInfo), {}),
                Type("thumb_name", "i", ""),
                Type("date_entry_modified", ("m", float), None),
                Type("date_entry_opened", ("o", float), None),
                Type("unreadable", "U", False),
                Type("audio_bit_rate", "r", 0),
                Type("audio_codec", "a", ""),
                Type("audio_codec_description", "A", ""),
                Type("bit_depth", "D", 0),
                Type("channels", "C", 2),
                Type("container_format", "c", ""),
                Type("device_name", "b", ""),
                Type("duration", "d", 0.0),
                Type("duration_time_base", "t", 0),
                Type("frame_rate_den", "y", 0),
                Type("frame_rate_num", "x", 0),
                Type("height", "h", 0),
                Type("meta_title", "n", ""),
                Type("properties", "p", {}),
                Type("sample_rate", "u", 0),
                Type("similarity_id", ("S", int), None),
                Type("video_codec", "v", ""),
                Type("video_codec_description", "V", ""),
                Type("width", "w", 0),
                Type("audio_languages", "l", []),
                Type("subtitle_languages", "L", []),
            ]
        )
