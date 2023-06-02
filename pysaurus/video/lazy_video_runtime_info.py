from pysaurus.core.schematizable import WithSchema, schema_prop
from pysaurus.video.video_runtime_info_schema import VideoRuntimeInfoSchema


class LazyVideoRuntimeInfo(WithSchema):
    __slots__ = ()
    SCHEMA = VideoRuntimeInfoSchema()

    size = schema_prop("size")
    mtime = schema_prop("mtime")
    driver_id = schema_prop("driver_id")
    is_file = schema_prop("is_file")
