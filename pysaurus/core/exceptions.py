class PysaurusError(Exception):
    pass


class NotDirectoryError(PysaurusError):
    def __init__(self, path):
        super().__init__(str(path))


class NotFileError(NotDirectoryError):
    pass


class NotDictionaryError(PysaurusError):
    pass


class UnsupportedOS(PysaurusError):
    pass


class UnknownVideoID(PysaurusError):
    pass


class UnknownUnreadableID(PysaurusError):
    pass


class UnknownVideoFilename(PysaurusError):
    pass


class UnknownUnreadableFilename(PysaurusError):
    pass


class MissingVideoNewTitle(PysaurusError):
    pass


class InvalidPageSize(PysaurusError):
    pass


class InvalidPageNumber(PysaurusError):
    pass


class FunctionParsingError(Exception):
    pass


class UnknownQuery(FunctionParsingError):
    pass


class InvalidQueryArgCount(FunctionParsingError):
    pass


class MissingQueryArg(FunctionParsingError):
    pass


class NoVideoClip(PysaurusError):
    pass


class InvalidVideoField(PysaurusError):
    pass
