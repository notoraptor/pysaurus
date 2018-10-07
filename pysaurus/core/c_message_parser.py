class CMessageParser(object):
    ERROR = '#ERROR'
    MESSAGE = '#MESSAGE'
    VIDEO_ERROR = '#VIDEO_ERROR'
    VIDEO_WARNING = '#VIDEO_WARNING'
    WARNING = '#WARNING'

    __prefixes__ = (ERROR, MESSAGE, VIDEO_ERROR, VIDEO_WARNING, WARNING)

    @classmethod
    def get_prefix(cls, line):
        for prefix in cls.__prefixes__:
            if line.startswith(prefix):
                return prefix
        return None
