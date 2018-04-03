SECONDS = 'SECONDS'
MILLISECONDS = 'MILLISECONDS'
MICROSECONDS = 'MICROSECONDS'

TIME_UNITS = {SECONDS, MILLISECONDS, MICROSECONDS}


class Duration(object):
    def __init__(self, value, unit):
        assert isinstance(value, (int, float))
        assert unit in TIME_UNITS
        self.value = value
        self.unit = unit

    def to_microseconds(self):
        if self.unit == MICROSECONDS:
            return self.value
        if self.unit == MILLISECONDS:
            return self.value * 1000
        if self.unit == SECONDS:
            return self.value * 1000000

    @classmethod
    def seconds(cls, value):
        return Duration(value, SECONDS)

    @classmethod
    def microseconds(cls, value):
        return Duration(value, MICROSECONDS)
