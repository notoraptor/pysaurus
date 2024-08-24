from pysaurus.core.schematizable import WithSchema, schema_prop
from pysaurus.video.video_runtime_info_schema import VIDEO_RUNTIME_INFO_SCHEMA


class LazyVideoRuntimeInfo(WithSchema):
    __slots__ = ()
    SCHEMA = VIDEO_RUNTIME_INFO_SCHEMA

    size = schema_prop("size")
    mtime = schema_prop("mtime")
    driver_id = schema_prop("driver_id")
    is_file = schema_prop("is_file")
