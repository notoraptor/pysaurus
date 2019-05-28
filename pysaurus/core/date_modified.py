from datetime import datetime


class DateModified:
    __slots__ = 'time',

    def __init__(self, float_timestamp):
        self.time = float_timestamp

    def __str__(self):
        return datetime.fromtimestamp(self.time).strftime('%Y-%m-%d %H:%M:%S')
