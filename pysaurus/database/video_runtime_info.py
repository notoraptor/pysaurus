from pysaurus.core.jsonable import Jsonable


class VideoRuntimeInfo(Jsonable):
    size: "s" = 0
    mtime: "m" = 0.0
    driver_id: (int, "d") = None
    is_file: "f" = False
    has_thumbnail: "t" = False

    @classmethod
    def ensure(cls, d):
        # type: (object) -> VideoRuntimeInfo
        return cls() if d is None else (d if isinstance(d, cls) else cls.from_dict(d))
