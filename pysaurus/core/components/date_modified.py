from datetime import datetime


class DateModified:
    __slots__ = 'time',

    def __init__(self, float_timestamp):
        self.time = float_timestamp

    def __str__(self):
        return datetime.fromtimestamp(self.time).strftime('%Y-%m-%d %H:%M:%S')

    def __hash__(self):
        return hash(self.time)

    def __eq__(self, other):
        return self.time == other.time

    def __lt__(self, other):
        return self.time < other.time
