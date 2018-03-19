class PysaurusException(Exception):
    def __init__(self, message=''):
        if not message:
            message = self.__doc__
        self.message = message
        super(PysaurusException, self).__init__(self.message)


class TypeException(PysaurusException):
    def __init__(self, expected, given):
        super(TypeException, self).__init__('Expected %s, got %s' % (expected, given))


class SequenceTypeException(PysaurusException):
    def __init__(self, given_type):
        super(SequenceTypeException, self).__init__('Expected an iterable, got %s' % given_type)
