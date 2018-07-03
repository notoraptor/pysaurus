from datetime import datetime


class Profile(object):

    def __init__(self, time_start, time_end):
        difference = time_end - time_start
        self.seconds = difference.seconds + difference.days * 24 * 3600
        self.microseconds = difference.microseconds

    def __str__(self):
        # str_second = 'seconds' if self.seconds else 'second'
        # str_microseconds = 'microseconds' if self.microseconds else 'microsecond'
        # return '%d %s %d %s' % (self.seconds, str_second, self.microseconds, str_microseconds)

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
        return ' '.join(pieces) if pieces else '0 sec'


class Profiler(object):
    __slots__ = {'__exit_message', '__placeholder', '__time_start', '__time_end', '__enter_message'}
    DEFAULT_PLACE_HOLDER = '__time__'

    def __init__(self, enter_message='', exit_message='', placeholder=DEFAULT_PLACE_HOLDER):
        self.__enter_message = enter_message
        self.__exit_message = exit_message
        self.__placeholder = placeholder or self.DEFAULT_PLACE_HOLDER
        self.__time_start = None
        self.__time_end = None

        if not self.__exit_message:
            self.__exit_message = self.__placeholder
        elif self.__placeholder not in self.__exit_message:
            self.__exit_message += ' ' + self.__placeholder

    def __enter__(self):
        if self.__enter_message:
            print(self.__enter_message)
        self.__time_start = datetime.now()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__time_end = datetime.now()
        profiling = Profile(self.__time_start, self.__time_end)
        print('[PROFILE]', self.__exit_message.replace(self.__placeholder, str(profiling)))
