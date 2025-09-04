from datetime import datetime


class Date:
    __slots__ = ("time",)

    def __init__(self, float_timestamp: float):
        self.time: float = float_timestamp

    def __str__(self):
        return datetime.fromtimestamp(self.time).strftime("%Y-%m-%d %H:%M:%S")

    def __hash__(self):
        return hash(self.time)

    def __float__(self):
        return self.time

    def __eq__(self, other):
        return self.time == other.time

    def __lt__(self, other):
        return self.time < other.time

    def __ge__(self, other):
        return self.time >= other.time

    @property
    def day(self):
        return datetime.fromtimestamp(self.time).strftime("%Y-%m-%d")

    @property
    def year(self) -> int:
        return int(datetime.fromtimestamp(self.time).strftime("%Y"))

    @staticmethod
    def now():
        return Date(datetime.now().timestamp())
