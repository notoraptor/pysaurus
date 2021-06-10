from pysaurus.core.database.viewport.viewtools.video_array import VideoArray


class Group:
    __slots__ = "field_value", "videos"

    def __init__(self, field_value, videos):
        self.field_value = field_value
        self.videos = VideoArray(videos)

    def __str__(self):
        return "Group(%s, %s)" % (self.field_value, len(self.videos))
