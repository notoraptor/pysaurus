from pysaurus.core.jsonable import Jsonable


class VideoRuntimeInfo(Jsonable):
    __short__ = {
        "size": "s",
        "mtime": "m",
        "driver_id": "d",
        "is_file": "f",
        "has_thumbnail": "t",
    }
    size: int = 0
    mtime: float = 0
    driver_id: int = None
    is_file: bool = False
    has_thumbnail: bool = False

    @classmethod
    def ensure(cls, d):
        # type: (object) -> VideoRuntimeInfo
        return cls() if d is None else (d if isinstance(d, cls) else cls.from_dict(d))
