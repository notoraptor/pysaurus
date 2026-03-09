from pysaurus.core.schematizable import Short, WithSchema


class LazyVideoRuntimeInfo(WithSchema):
    __slots__ = ()
    size: Short["s", int] = 0
    mtime: Short["m", float] = 0.0
    driver_id: Short["d", int] = None
    is_file: Short["f", bool] = False
