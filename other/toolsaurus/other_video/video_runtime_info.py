from other.toolsaurus.jsonable import Jsonable


class VideoRuntimeInfo(Jsonable):
    size: "s" = 0
    mtime: "m" = 0.0
    driver_id: (int, "d") = None
    is_file: "f" = False
    has_thumbnail: "t" = False
