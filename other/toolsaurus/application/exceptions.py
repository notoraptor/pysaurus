from pysaurus.application.exceptions import PysaurusError


class UnknownVideoID(PysaurusError):
    pass


class InvalidPageNumber(PysaurusError):
    pass


class InvalidPageSize(PysaurusError):
    pass


class MissingVideoNewTitle(PysaurusError):
    pass


class UnknownVideoFilename(PysaurusError):
    pass
