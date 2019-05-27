from datetime import datetime

from pysaurus.core import notifier, notifications
from pysaurus.core.profile import Profile


class Profiler(object):
    __slots__ = ('__title', '__time_start', '__time_end')
    DEFAULT_PLACE_HOLDER = '__time__'

    def __init__(self, title):
        self.__title = title
        self.__time_start = None
        self.__time_end = None

    def __enter__(self):
        notifier.notify(notifications.ProfilingStart(self.__title))
        self.__time_start = datetime.now()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__time_end = datetime.now()
        profiling = Profile(self.__time_start, self.__time_end)
        notifier.notify(notifications.ProfilingEnd(self.__title, profiling))
