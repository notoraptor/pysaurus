class VideoDuration(object):
    __slots__ = ('days', 'hours', 'minutes', 'seconds', 'microseconds', 'comparable_duration', 'video')

    def __init__(self, video):
        """ Video duration is number of seconds * video time base.
            So, number of seconds = video duration / video time base.
            :param video: video to get duration.
            :type video: pysaurus.core.video.Video
        """
        self.video = video

        remaining_time = self.video.duration % self.video.duration_time_base
        solid_seconds = self.video.duration // self.video.duration_time_base
        solid_minutes = solid_seconds // 60
        solid_hours = solid_minutes // 60

        self.days = solid_hours // 24
        self.hours = solid_hours % 24
        self.minutes = solid_minutes % 60
        self.seconds = solid_seconds % 60
        self.microseconds = round(1000000 * remaining_time / self.video.duration_time_base)

        # Comparable duration is video duration round to microseconds.
        self.comparable_duration = round(self.video.duration * 1000000 / self.video.duration_time_base)

    def __hash__(self):
        return hash(self.comparable_duration)

    def __eq__(self, other):
        return isinstance(other, VideoDuration) and self.comparable_duration == other.comparable_duration

    def __ne__(self, other):
        return isinstance(other, VideoDuration) and self.comparable_duration != other.comparable_duration

    def __lt__(self, other):
        return isinstance(other, VideoDuration) and self.comparable_duration < other.comparable_duration

    def __gt__(self, other):
        return isinstance(other, VideoDuration) and self.comparable_duration > other.comparable_duration

    def __le__(self, other):
        return isinstance(other, VideoDuration) and self.comparable_duration <= other.comparable_duration

    def __ge__(self, other):
        return isinstance(other, VideoDuration) and self.comparable_duration >= other.comparable_duration

    def __str__(self):
        view = []
        if self.days:
            view.append('%02dd' % self.days)
        if self.hours:
            view.append('%02dh' % self.hours)
        if self.minutes:
            view.append('%02dm' % self.minutes)
        if self.seconds:
            view.append('%02ds' % self.seconds)
        if self.microseconds:
            view.append('%06dms' % self.microseconds)
        return ' '.join(view)
