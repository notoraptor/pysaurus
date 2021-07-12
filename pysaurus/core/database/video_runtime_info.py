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

    def to_dict(self):
        return {
            "s": self.size,
            "m": self.mtime,
            "d": self.driver_id,
            "f": self.is_file,
            "t": self.has_thumbnail,
        }

    @classmethod
    def from_dict(cls, dct: dict):
        return cls(
            size=dct.get("s", 0),
            mtime=dct.get("m", 0),
            driver_id=dct.get("d", None),
            is_file=dct.get("f", False),
            has_thumbnail=dct.get("t", False),
        )

    @classmethod
    def ensure(cls, d):
        return cls() if d is None else (d if isinstance(d, cls) else cls.from_dict(d))
