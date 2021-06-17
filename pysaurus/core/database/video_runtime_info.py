class VideoRuntimeInfo:
    __slots__ = "is_file", "size", "mtime", "driver_id", "has_thumbnail"

    def __init__(
        self,
        size: int = 0,
        mtime: float = 0,
        driver_id: int = None,
        is_file: bool = False,
        has_thumbnail: bool = False,
    ):
        self.size = size
        self.mtime = mtime
        self.driver_id = driver_id
        self.is_file = is_file
        self.has_thumbnail = has_thumbnail
