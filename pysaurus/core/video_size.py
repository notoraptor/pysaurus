from pysaurus.core.constants import BYTES, KILO_BYTES, MEGA_BYTES, GIGA_BYTES, SIZE_UNIT_TO_STRING


class VideoSize(object):
    __slots__ = ('video', 'unit')

    def __init__(self, video):
        """
        :param video:
        :type video: pysaurus.video.Video
        """
        self.video = video
        if self.video.size // GIGA_BYTES:
            self.unit = GIGA_BYTES
        elif self.video.size // MEGA_BYTES:
            self.unit = MEGA_BYTES
        elif self.video.size // KILO_BYTES:
            self.unit = KILO_BYTES
        else:
            self.unit = BYTES

    @property
    def comparable_size(self):
        return self.video.size

    @property
    def size(self):
        return self.video.size / self.unit

    def __hash__(self):
        return hash(self.comparable_size)

    def __eq__(self, other):
        return isinstance(other, VideoSize) and self.comparable_size == other.comparable_size

    def __ne__(self, other):
        return isinstance(other, VideoSize) and self.comparable_size != other.comparable_size

    def __lt__(self, other):
        return isinstance(other, VideoSize) and self.comparable_size < other.comparable_size

    def __gt__(self, other):
        return isinstance(other, VideoSize) and self.comparable_size > other.comparable_size

    def __le__(self, other):
        return isinstance(other, VideoSize) and self.comparable_size <= other.comparable_size

    def __ge__(self, other):
        return isinstance(other, VideoSize) and self.comparable_size >= other.comparable_size

    def __str__(self):
        return '%s %s' % (round(self.size, 2), SIZE_UNIT_TO_STRING[self.unit])
