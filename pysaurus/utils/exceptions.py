class PysaurusException(Exception):
    def __init__(self, message=''):
        self.message = (message or self.__doc__).strip()
        super(PysaurusException, self).__init__(self.message)


class TypeException(PysaurusException):
    def __init__(self, expected, given):
        super(TypeException, self).__init__('Expected %s, got %s' % (expected, given))


class SequenceTypeException(PysaurusException):
    def __init__(self, given_type):
        super(SequenceTypeException, self).__init__('Expected an iterable, got %s' % given_type)


class FFmpegException(PysaurusException):
    def __init__(self, msg=''):
        super(FFmpegException, self).__init__(msg)


class FFprobeException(FFmpegException):
    pass


class VideoIdException(PysaurusException):
    """ Invalid video ID. """


class DuplicateEntryException(PysaurusException):
    """ Duplicate video entry in database. """
