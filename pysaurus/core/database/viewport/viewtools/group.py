from pysaurus.core.database.viewport.viewtools.video_array import VideoArray


class Group:
    __slots__ = "field_value", "videos"

    def __init__(self, field_value, videos):
        self.field_value = field_value
        self.videos = VideoArray(videos)

    def is_defined(self):
        return self.field_value is not None

    @property
    def field(self):
        return self.field_value

    @property
    def count(self):
        return len(self.videos)

    @property
    def length(self):
        return len(str(self.field_value))
