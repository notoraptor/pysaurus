class PysaurusError(Exception):
    pass


class NotDirectoryError(PysaurusError):
    def __init__(self, path):
        super().__init__(str(path))


class NotFileError(NotDirectoryError):
    pass


class NotDictionaryError(PysaurusError):
    pass
