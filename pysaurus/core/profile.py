class Profile(object):
    __slots__ = ('seconds', 'microseconds')

    def __init__(self, time_start, time_end):
        difference = time_end - time_start
        self.seconds = difference.seconds + difference.days * 24 * 3600
        self.microseconds = difference.microseconds

    def __str__(self):
        hours = self.seconds // 3600
        minutes = (self.seconds - 3600 * hours) // 60
        seconds = (self.seconds - 3600 * hours - 60 * minutes)
        pieces = []
        if hours:
            pieces.append('%d h' % hours)
        if minutes:
            pieces.append('%d min' % minutes)
        if seconds:
            pieces.append('%d sec' % seconds)
        if self.microseconds:
            pieces.append('%d microsec' % self.microseconds)
        return '(%s)' % (' '.join(pieces) if pieces else '0 sec')
