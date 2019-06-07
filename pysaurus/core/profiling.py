from datetime import datetime

from pysaurus.core import notifications
from pysaurus.core.notifier import DEFAULT_NOTIFIER


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


class Profiler(object):
    __slots__ = ('__title', '__time_start', '__time_end', '__notifier')
    DEFAULT_PLACE_HOLDER = '__time__'

    def __init__(self, title, notifier=None):
        self.__title = title
        self.__notifier = notifier or DEFAULT_NOTIFIER
        self.__time_start = None
        self.__time_end = None

    def __enter__(self):
        self.__notifier.notify(notifications.ProfilingStart(self.__title))
        self.__time_start = datetime.now()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__time_end = datetime.now()
        profiling = Profile(self.__time_start, self.__time_end)
        self.__notifier.notify(notifications.ProfilingEnd(self.__title, profiling))
