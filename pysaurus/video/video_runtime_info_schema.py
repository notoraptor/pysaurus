from pysaurus.core.jsonable import Type
from pysaurus.core.schematizable import Schema


class VideoRuntimeInfoSchema(Schema):
    __slots__ = ()

    def __init__(self):
        super().__init__(
            [
                Type("size", "s", 0),
                Type("mtime", "m", 0.0),
                Type("driver_id", (int, "d"), None),
                Type("is_file", "f", False),
                Type("has_thumbnail", "t", False),
            ]
        )
