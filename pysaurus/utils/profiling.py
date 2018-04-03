from datetime import datetime


class Profiling(object):

    def __init__(self, time_start, time_end):
        difference = time_end - time_start
        self.seconds = difference.seconds + difference.days * 24 * 3600
        self.microseconds = difference.microseconds

    def __str__(self):
        str_second = 'seconds' if self.seconds else 'second'
        str_microseconds = 'microseconds' if self.microseconds else 'microsecond'
        return '%d %s %d %s' % (self.seconds, str_second, self.microseconds, str_microseconds)


class Profiler(object):
    __slots__ = {'__message_format', '__placeholder', '__time_start', '__time_end', '__enter_message'}

    def __init__(self, enter_message='', exit_message='', placeholder='__time__'):
        self.__message_format = exit_message
        self.__placeholder = placeholder
        self.__enter_message = enter_message
        self.__time_start = None
        self.__time_end = None

    def __enter__(self):
        if self.__enter_message:
            print(self.__enter_message)
        self.__time_start = datetime.now()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__time_end = datetime.now()
        profiling = Profiling(self.__time_start, self.__time_end)
        print('[PROFILE] ', end='')
        if self.__message_format == '':
            print(profiling)
        elif self.__placeholder not in self.__message_format:
            print(self.__message_format, profiling)
        else:
            print(self.__message_format.replace(self.__placeholder, str(profiling)))
