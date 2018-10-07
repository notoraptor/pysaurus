class VideoDuration(object):
    __slots__ = ('days', 'hours', 'minutes', 'seconds', 'nb_seconds', 'video')

    def __init__(self, video):
        """ Video duration is number of seconds * video time base.
            So, number of seconds = video duration / video time base.
            :param video: video to get duration.
            :type video: pysaurus.core.video.Video
        """
        self.video = video
        nb_seconds = round(self.video.duration / self.video.duration_time_base)
        minutes = nb_seconds // 60
        seconds = nb_seconds % 60
        hours = minutes // 60
        minutes = minutes % 60
        days = hours // 24
        hours = hours % 24
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.nb_seconds = nb_seconds

    @property
    def _comparable_duration(self):
        # return self.video.duration
        # return self.video.duration // self.video.duration_time_base
        return self.nb_seconds

    def __hash__(self):
        return hash(self._comparable_duration)

    def __eq__(self, other):
        return isinstance(other, VideoDuration) and self._comparable_duration == other._comparable_duration

    def __ne__(self, other):
        return isinstance(other, VideoDuration) and self._comparable_duration != other._comparable_duration

    def __lt__(self, other):
        return isinstance(other, VideoDuration) and self._comparable_duration < other._comparable_duration

    def __gt__(self, other):
        return isinstance(other, VideoDuration) and self._comparable_duration > other._comparable_duration

    def __le__(self, other):
        return isinstance(other, VideoDuration) and self._comparable_duration <= other._comparable_duration

    def __ge__(self, other):
        return isinstance(other, VideoDuration) and self._comparable_duration >= other._comparable_duration

    def __str__(self):
        view = []
        if self.days:
            view.append('%02dd' % self.days)
        if self.hours:
            view.append('%02dh' % self.hours)
        if self.minutes:
            view.append('%02dmin' % self.minutes)
        if self.seconds:
            view.append('%02dsec' % self.seconds)
        return ''.join(view)
