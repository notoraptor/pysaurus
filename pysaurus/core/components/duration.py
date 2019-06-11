class Duration(object):
    __slots__ = ('days', 'hours', 'minutes', 'seconds', 'microseconds', 'total_microseconds')

    def __init__(self, microseconds):
        solid_seconds = microseconds // 1000000
        solid_minutes = solid_seconds // 60
        solid_hours = solid_minutes // 60

        self.days = solid_hours // 24
        self.hours = solid_hours % 24
        self.minutes = solid_minutes % 60
        self.seconds = solid_seconds % 60
        self.microseconds = microseconds % 1000000

        # Comparable duration is video duration round to microseconds.
        self.total_microseconds = microseconds

    def __hash__(self):
        return hash(self.total_microseconds)

    def __eq__(self, other):
        return self.total_microseconds == other.total_microseconds

    def __ne__(self, other):
        return self.total_microseconds != other.total_microseconds

    def __lt__(self, other):
        return self.total_microseconds < other.total_microseconds

    def __gt__(self, other):
        return self.total_microseconds > other.total_microseconds

    def __le__(self, other):
        return self.total_microseconds <= other.total_microseconds

    def __ge__(self, other):
        return self.total_microseconds >= other.total_microseconds

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

    def to_json(self):
        return str(self)
