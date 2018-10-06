KO = 1024
MO = KO * KO
GO = KO * KO * KO

class Size(object):
    __slots__ = ('video', 'size', 'unit')
    def __init__(self, video):
        """
        :param video:
        :type video: pysaurus.video.Video
        """
        self.video = video
        if self.video.size // GO:
            self.size = self.video.size / GO
            self.unit = 'Go'
        elif self.video.size // MO:
            self.size = self.video.size / MO
            self.unit = 'Mo'
        elif self.video.size // KO:
            self.size = self.video.size / KO
            self.unit = 'Ko'
        else:
            self.size = self.video.size
            self.unit = 'o'
    def __str__(self):
        return '%s %s' % (round(self.size, 2), self.unit)