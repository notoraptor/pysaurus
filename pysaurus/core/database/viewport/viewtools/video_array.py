from pysaurus.core.database.video_state import VideoState
from pysaurus.core.database.viewport.viewtools.lookup_array import LookupArray


class VideoArray(LookupArray[VideoState]):
    __slots__ = ()

    def __init__(self, content=()):
        super().__init__(VideoState, content, lambda video: video.filename)
