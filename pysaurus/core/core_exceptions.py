class NotAFileError(NotADirectoryError):
    pass


class UnsupportedSystemError(SystemError):
    pass


class ZeroLengthError(ArithmeticError):
    pass


class DiskSpaceError(OSError):
    pass


class NoShortPathError(OSError):
    pass


# TODO Use application error logic (see class doc below)
class ApplicationError(Exception):
    """Base exception to be used to represent an application error.

    An application error is intended to be caught and handled
    by application and runtime, while a non-application error
    should be unexpected and must then make program crash.
    """
