O = 1
KO = 1024
MO = KO * KO
GO = KO * KO * KO
UNIT_TO_STRING = {
    O: 'o',
    KO: 'Ko',
    MO: 'Mo',
    GO: 'Go'
}


class VideoSize(object):
    __slots__ = ('video', 'size', 'unit')

    def __init__(self, video):
        """
        :param video:
        :type video: pysaurus.video.Video
        """
        self.video = video
        self.unit = O
        if self.video.size // GO:
            self.unit = GO
        elif self.video.size // MO:
            self.unit = MO
        elif self.video.size // KO:
            self.unit = KO
        self.size = self.video.size / self.unit

    @property
    def _comparable_duration(self):
        return self.video.size

    def __hash__(self):
        return hash(self._comparable_duration)

    def __eq__(self, other):
        return isinstance(other, VideoSize) and self._comparable_duration == other._comparable_duration

    def __ne__(self, other):
        return isinstance(other, VideoSize) and self._comparable_duration != other._comparable_duration

    def __lt__(self, other):
        return isinstance(other, VideoSize) and self._comparable_duration < other._comparable_duration

    def __gt__(self, other):
        return isinstance(other, VideoSize) and self._comparable_duration > other._comparable_duration

    def __le__(self, other):
        return isinstance(other, VideoSize) and self._comparable_duration <= other._comparable_duration

    def __ge__(self, other):
        return isinstance(other, VideoSize) and self._comparable_duration >= other._comparable_duration

    def __str__(self):
        return '%s %s' % (round(self.size, 2), UNIT_TO_STRING[self.unit])
