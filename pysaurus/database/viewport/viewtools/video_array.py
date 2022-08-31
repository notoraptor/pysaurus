from pysaurus.database.video import Video
from pysaurus.database.viewport.viewtools.lookup_array import LookupArray


class VideoArray(LookupArray[Video]):
    __slots__ = ()

    def __init__(self, content=()):
        super().__init__(Video, content, lambda video: video.filename)
