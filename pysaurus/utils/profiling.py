class Profiling(object):

    def __init__(self, time_start, time_end):
        difference = time_end - time_start
        self.seconds = difference.seconds + difference.days * 24 * 3600
        self.microseconds = difference.microseconds

    def __str__(self):
        str_second = 'seconds' if self.seconds else 'second'
        str_microseconds = 'microseconds' if self.microseconds else 'microsecond'
        return '%d %s %d %s' % (self.seconds, str_second, self.microseconds, str_microseconds)