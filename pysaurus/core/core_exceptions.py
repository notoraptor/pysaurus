class NotAFileError(NotADirectoryError):
    pass


class UnsupportedSystemError(SystemError):
    pass


class ZeroLengthError(ArithmeticError):
    pass


class DiskSpaceError(OSError):
    pass


class NoShortPathError(WindowsError):
    pass
