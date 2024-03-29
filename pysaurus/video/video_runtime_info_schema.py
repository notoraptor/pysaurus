from pysaurus.core.json_type import Type
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
            ]
        )
